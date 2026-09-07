package com.casait.emtgateway.ui

import android.content.IntentFilter
import android.hardware.usb.UsbManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.*
import com.casait.emtgateway.domain.model.InternetState
import com.casait.emtgateway.domain.model.TransportType
import com.casait.emtgateway.gateway.GatewayManager
import com.casait.emtgateway.gateway.UsbDeviceReceiver
import com.casait.emtgateway.ui.screens.ConnectionScreen
import com.casait.emtgateway.ui.screens.GatewayScreen
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {

    private lateinit var gatewayManager: GatewayManager
    private var usbReceiver: UsbDeviceReceiver? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        gatewayManager = GatewayManager(this)

        registerUsbReceiver()

        setContent {
            var currentScreen by remember { mutableStateOf("dashboard") }
            val state by gatewayManager.gatewayState.collectAsState()
            val vital by gatewayManager.latestVital.collectAsState()
            val scope = rememberCoroutineScope()

            // Auto-connect wired link on startup
            LaunchedEffect(Unit) {
                val ok1 = gatewayManager.connect(TransportType.ETHERNET, "127.0.0.1", 8000)
                if (!ok1) {
                    gatewayManager.connect(TransportType.ETHERNET, "192.168.29.239", 8000)
                }
            }

            if (currentScreen == "dashboard") {
                GatewayScreen(
                    state = state,
                    vital = vital,
                    onNewCaseClick = {
                        gatewayManager.prepareNewCase()
                    },
                    onStartCaseClick = { name, age, sex, classification, esiLevel ->
                        gatewayManager.createAndStartCase(name, age, sex, classification, esiLevel)
                    },
                    onCloseCaseClick = {
                        gatewayManager.closeCurrentCase()
                    },
                    onToggleInternet = {
                        val isOnline = state.internetState == InternetState.ONLINE
                        gatewayManager.syncManager.setInternetState(!isOnline)
                    }
                )
            } else {
                ConnectionScreen(
                    currentTransport = state.transportType,
                    currentIp = state.monitorIp,
                    currentPort = state.monitorPort,
                    onSaveAndConnect = { transport, ip, port ->
                        scope.launch {
                            gatewayManager.connect(transport, ip, port)
                            currentScreen = "dashboard"
                        }
                    },
                    onBack = { currentScreen = "dashboard" }
                )
            }
        }
    }

    private fun registerUsbReceiver() {
        usbReceiver = UsbDeviceReceiver(
            onDeviceAttached = { gatewayManager.onUsbDeviceAttached() },
            onDeviceDetached = { gatewayManager.onUsbDeviceDetached() },
            onPermissionResult = { _, granted ->
                if (granted) {
                    gatewayManager.onUsbDeviceAttached()
                }
            }
        )
        val filter = IntentFilter().apply {
            addAction(UsbManager.ACTION_USB_DEVICE_ATTACHED)
            addAction(UsbManager.ACTION_USB_DEVICE_DETACHED)
            addAction(UsbDeviceReceiver.ACTION_USB_PERMISSION)
        }
        @Suppress("UnspecifiedRegisterReceiverFlag")
        registerReceiver(usbReceiver, filter)
    }

    override fun onDestroy() {
        super.onDestroy()
        usbReceiver?.let { unregisterReceiver(it) }
    }
}
