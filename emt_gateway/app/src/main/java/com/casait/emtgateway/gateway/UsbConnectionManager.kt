package com.casait.emtgateway.gateway

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.hardware.usb.*
import android.util.Log
import com.casait.emtgateway.data.wired.EthernetConnection
import com.casait.emtgateway.data.wired.UsbConnection
import com.casait.emtgateway.domain.model.MonitorConnectionState
import com.casait.emtgateway.domain.model.TransportType
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.net.NetworkInterface

class UsbConnectionManager(private val context: Context) {
    private val TAG = "UsbConnectionManager"
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val mutex = Mutex()

    private val usbManager = context.getSystemService(Context.USB_SERVICE) as UsbManager

    private val _connectionState = MutableStateFlow(MonitorConnectionState.DISCONNECTED)
    val connectionState: StateFlow<MonitorConnectionState> = _connectionState.asStateFlow()

    private val _transportType = MutableStateFlow(TransportType.ETHERNET)
    val transportType: StateFlow<TransportType> = _transportType.asStateFlow()

    private val incomingDataFlow = MutableSharedFlow<String>(extraBufferCapacity = 256)

    private var activeUsbConnection: UsbConnection? = null
    private var activeEthernetConnection: EthernetConnection? = null
    private var readerJob: Job? = null

    // Connection Health & Status Flags
    var usbDeviceAttached: Boolean = false
        private set
    var usbPermissionGranted: Boolean = false
        private set
    var readerRunning: Boolean = false
        private set

    init {
        Log.i(TAG, "USB_CONNECTION_MANAGER_INITIALIZED: Single authoritative USB connection manager started.")
        startAutoDiscoveryLoop()
    }

    private fun startAutoDiscoveryLoop() {
        scope.launch {
            while (isActive) {
                delay(2000)
                mutex.withLock {
                    val state = _connectionState.value
                    if (state == MonitorConnectionState.DISCONNECTED || state == MonitorConnectionState.MONITOR_DATA_LOST) {
                        Log.d(TAG, "USB_AUTO_DISCOVERY_LOOP: Checking connected hardware & network interfaces...")
                        performConnectionAttemptLocked()
                    }
                }
            }
        }
    }

    suspend fun discoverAndConnect(): Boolean = mutex.withLock {
        Log.i(TAG, "USB_EXPLICIT_DISCOVER_REQUESTED")
        return performConnectionAttemptLocked()
    }

    private suspend fun performConnectionAttemptLocked(): Boolean {
        // 1. Freshly query attached USB Host devices
        val deviceList = usbManager.deviceList
        usbDeviceAttached = deviceList.isNotEmpty()

        if (usbDeviceAttached) {
            val device = deviceList.values.first()
            Log.i(TAG, "USB_DEVICE_FOUND: ${device.deviceName} (Vendor=${device.vendorId}, Product=${device.productId})")
            if (!usbManager.hasPermission(device)) {
                usbPermissionGranted = false
                Log.w(TAG, "USB_PERMISSION_REQUIRED for ${device.deviceName}")
                _connectionState.value = MonitorConnectionState.CONNECTING
                requestUsbPermission(device)
                return false
            } else {
                usbPermissionGranted = true
                Log.i(TAG, "USB_PERMISSION_GRANTED for ${device.deviceName}")
            }

            _transportType.value = TransportType.USB
            _connectionState.value = MonitorConnectionState.CONNECTING

            stopReaderLocked()
            val usbConn = UsbConnection(context)
            val success = usbConn.connect()
            if (success) {
                activeUsbConnection = usbConn
                _connectionState.value = MonitorConnectionState.CONNECTED
                Log.i(TAG, "USB_CONNECTED: Successfully connected to USB Host device ${device.deviceName}")
                startReaderLocked(usbConn.observeIncomingData())
                return true
            }
        }

        // 2. Discover USB Tethering / Ethernet / Network Gateway endpoints
        _transportType.value = TransportType.ETHERNET
        _connectionState.value = MonitorConnectionState.CONNECTING

        stopReaderLocked()
        val ethConn = EthernetConnection()

        val candidateIps = discoverGatewayIps()
        for (candidateIp in candidateIps) {
            Log.i(TAG, "USB_CONNECTING: Attempting connection to $candidateIp:8000")
            ethConn.configureEndpoint(candidateIp, 8000)
            if (ethConn.connect()) {
                activeEthernetConnection = ethConn
                _connectionState.value = MonitorConnectionState.CONNECTED
                Log.i(TAG, "USB_CONNECTED: Successfully established socket to $candidateIp:8000")
                startReaderLocked(ethConn.observeIncomingData())
                return true
            }
        }

        Log.w(TAG, "USB_DISCONNECTED: All USB connection attempts failed. Retrying...")
        _connectionState.value = MonitorConnectionState.DISCONNECTED
        return false
    }

    private fun discoverGatewayIps(): List<String> {
        val candidates = mutableListOf("127.0.0.1", "192.168.42.129", "192.168.43.1", "10.0.2.2", "192.168.29.239", "10.81.114.142", "172.100.84.98")
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val ni = interfaces.nextElement()
                val addresses = ni.inetAddresses
                while (addresses.hasMoreElements()) {
                    val addr = addresses.nextElement()
                    if (!addr.isLoopbackAddress && addr.hostAddress != null) {
                        val hostIp = addr.hostAddress!!
                        if (hostIp.contains(".")) {
                            val prefix = hostIp.substringBeforeLast(".")
                            val gateway = "$prefix.1"
                            if (!candidates.contains(gateway)) candidates.add(0, gateway)
                            val hostTetherIp = "$prefix.129"
                            if (!candidates.contains(hostTetherIp)) candidates.add(0, hostTetherIp)
                            val hostTetherIp142 = "$prefix.142"
                            if (!candidates.contains(hostTetherIp142)) candidates.add(0, hostTetherIp142)
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error inspecting network interfaces", e)
        }
        return candidates
    }

    private fun requestUsbPermission(device: UsbDevice) {
        try {
            Log.i(TAG, "Requesting USB permission for device: ${device.deviceName}")
            val intent = Intent("com.casait.emtgateway.USB_PERMISSION")
            val flags = PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
            val permissionIntent = PendingIntent.getBroadcast(context, 0, intent, flags)
            usbManager.requestPermission(device, permissionIntent)
        } catch (e: Exception) {
            Log.e(TAG, "Error requesting USB permission", e)
        }
    }

    suspend fun onUsbDeviceAttached(device: UsbDevice?) = mutex.withLock {
        Log.i(TAG, "USB_DEVICE_ATTACHED: New hardware attached: ${device?.deviceName}")
        usbDeviceAttached = true
        performConnectionAttemptLocked()
    }

    suspend fun onUsbDeviceDetached(device: UsbDevice?) = mutex.withLock {
        Log.i(TAG, "USB_DEVICE_DETACHED: Hardware detached: ${device?.deviceName}")
        usbDeviceAttached = false
        usbPermissionGranted = false
        disconnectLocked()
    }

    suspend fun disconnect() = mutex.withLock {
        disconnectLocked()
    }

    private suspend fun disconnectLocked() {
        Log.i(TAG, "USB_DISCONNECTED: Stopping reader & nullifying connection references.")
        stopReaderLocked()

        try {
            activeUsbConnection?.disconnect()
        } catch (e: Exception) {
            Log.e(TAG, "Error disconnecting USB Host", e)
        }
        activeUsbConnection = null

        try {
            activeEthernetConnection?.disconnect()
        } catch (e: Exception) {
            Log.e(TAG, "Error disconnecting Ethernet socket", e)
        }
        activeEthernetConnection = null

        _connectionState.value = MonitorConnectionState.DISCONNECTED
    }

    private fun startReaderLocked(flow: Flow<String>) {
        stopReaderLocked()
        readerRunning = true
        Log.i(TAG, "USB_READER_STARTED: Launching single active reader coroutine.")
        readerJob = scope.launch {
            try {
                flow.collect { data ->
                    _connectionState.value = MonitorConnectionState.MONITORING
                    incomingDataFlow.emit(data)
                }
            } catch (e: CancellationException) {
                Log.i(TAG, "USB_READER_STOPPED: Reader job cancelled cleanly.")
            } catch (e: Exception) {
                Log.e(TAG, "Error in USB Reader job", e)
            } finally {
                readerRunning = false
                Log.i(TAG, "USB_READER_STOPPED: Reader job terminated.")
            }
        }
    }

    private fun stopReaderLocked() {
        if (readerJob != null) {
            Log.i(TAG, "USB_READER_STOPPED: Cancelling existing reader job.")
            readerJob?.cancel()
            readerJob = null
        }
        readerRunning = false
    }

    fun observeIncomingData(): Flow<String> = incomingDataFlow.asSharedFlow()

    fun setConnectedState(state: MonitorConnectionState) {
        _connectionState.value = state
    }
}
