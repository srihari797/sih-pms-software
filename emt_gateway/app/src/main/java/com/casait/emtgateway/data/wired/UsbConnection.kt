package com.casait.emtgateway.data.wired

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.hardware.usb.*
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.withContext

class UsbConnection(private val context: Context) : WiredConnection {
    private val TAG = "UsbConnection"
    private val usbManager: UsbManager = context.getSystemService(Context.USB_SERVICE) as UsbManager
    private var connection: UsbDeviceConnection? = null
    private var endpointIn: UsbEndpoint? = null
    private var endpointOut: UsbEndpoint? = null
    private var isConnectedState = false

    private val incomingSharedFlow = MutableSharedFlow<String>(extraBufferCapacity = 64)

    override suspend fun connect(): Boolean = withContext(Dispatchers.IO) {
        val deviceList = usbManager.deviceList
        if (deviceList.isEmpty()) {
            Log.w(TAG, "No USB host devices found attached to Android device.")
            return@withContext false
        }

        val device: UsbDevice = deviceList.values.first()
        if (!usbManager.hasPermission(device)) {
            Log.i(TAG, "Requesting USB permission for device: ${device.deviceName}")
            val intent = Intent("com.casait.emtgateway.USB_PERMISSION")
            val flags = PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
            val permissionIntent = PendingIntent.getBroadcast(context, 0, intent, flags)
            usbManager.requestPermission(device, permissionIntent)
            return@withContext false
        }

        val usbInterface: UsbInterface = device.getInterface(0)
        val conn = usbManager.openDevice(device) ?: return@withContext false
        conn.claimInterface(usbInterface, true)

        for (i in 0 until usbInterface.endpointCount) {
            val ep = usbInterface.getEndpoint(i)
            if (ep.direction == UsbConstants.USB_DIR_IN) {
                endpointIn = ep
            } else if (ep.direction == UsbConstants.USB_DIR_OUT) {
                endpointOut = ep
            }
        }

        connection = conn
        isConnectedState = true
        Log.i(TAG, "USB Connection successfully opened to ${device.deviceName}")
        return@withContext true
    }

    override suspend fun disconnect() = withContext(Dispatchers.IO) {
        isConnectedState = false
        try {
            connection?.close()
        } catch (e: Exception) {
            Log.e(TAG, "Error closing USB connection", e)
        }
        connection = null
        endpointIn = null
        endpointOut = null
    }

    override suspend fun send(data: ByteArray): Boolean = withContext(Dispatchers.IO) {
        val conn = connection ?: return@withContext false
        val epOut = endpointOut ?: return@withContext false
        val bytesSent = conn.bulkTransfer(epOut, data, data.size, 1000)
        return@withContext bytesSent >= 0
    }

    override fun observeIncomingData(): Flow<String> = incomingSharedFlow.asSharedFlow()

    override fun isConnected(): Boolean = isConnectedState

    override fun getTransportName(): String = "USB_HOST"
}
