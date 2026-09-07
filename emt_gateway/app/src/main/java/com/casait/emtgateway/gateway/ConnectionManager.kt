package com.casait.emtgateway.gateway

import android.content.Context
import com.casait.emtgateway.domain.model.MonitorConnectionState
import com.casait.emtgateway.domain.model.TransportType
import kotlinx.coroutines.flow.StateFlow

class ConnectionManager(context: Context) {

    val usbConnectionManager = UsbConnectionManager(context)

    val connectionState: StateFlow<MonitorConnectionState> = usbConnectionManager.connectionState
    val transportType: StateFlow<TransportType> = usbConnectionManager.transportType

    fun setConnectedState(state: MonitorConnectionState) {
        usbConnectionManager.setConnectedState(state)
    }

    fun setTransportType(type: TransportType, host: String = "127.0.0.1", port: Int = 8000) {
        // Managed dynamically by UsbConnectionManager
    }

    suspend fun connect(): Boolean {
        return usbConnectionManager.discoverAndConnect()
    }

    suspend fun disconnect() {
        usbConnectionManager.disconnect()
    }

    fun observeIncomingData() = usbConnectionManager.observeIncomingData()
}
