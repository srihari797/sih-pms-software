package com.casait.emtgateway.data.wired

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.withContext
import okhttp3.*
import java.util.concurrent.TimeUnit

class EthernetConnection(
    private var host: String = "127.0.0.1",
    private var port: Int = 8000
) : WiredConnection {

    private val TAG = "EthernetConnection"

    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .pingInterval(5, TimeUnit.SECONDS)
        .build()

    private var webSocket: WebSocket? = null
    private var isConnectedState = false

    private val incomingSharedFlow = MutableSharedFlow<String>(
        replay = 1,
        extraBufferCapacity = 256,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )

    fun configureEndpoint(newHost: String, newPort: Int) {
        this.host = newHost
        this.port = newPort
    }

    override suspend fun connect(): Boolean = withContext(Dispatchers.IO) {
        if (isConnectedState && webSocket != null) {
            return@withContext true
        }

        val candidateHosts = mutableListOf(host)
        listOf("127.0.0.1", "10.0.2.2", "192.168.42.129", "192.168.43.1", "192.168.29.239", "10.81.114.142", "172.100.84.98").forEach { ip ->
            if (!candidateHosts.contains(ip)) candidateHosts.add(ip)
        }

        for (candidateIp in candidateHosts) {
            val url = "ws://$candidateIp:$port/ws/monitor/P001"
            Log.i(TAG, "Attempting WebSocket connection to candidate URL: $url")
            val request = Request.Builder().url(url).build()

            var connectedThisTry = false
            val ws = client.newWebSocket(request, object : WebSocketListener() {
                override fun onOpen(webSocket: WebSocket, response: Response) {
                    Log.i(TAG, "WebSocket OPENED successfully to $url")
                    isConnectedState = true
                    connectedThisTry = true
                    host = candidateIp
                }

                override fun onMessage(webSocket: WebSocket, text: String) {
                    Log.i(TAG, "WebSocket RECEIVED payload: $text")
                    incomingSharedFlow.tryEmit(text)
                }

                override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                    Log.i(TAG, "WebSocket CLOSED: code=$code, reason=$reason")
                    isConnectedState = false
                    this@EthernetConnection.webSocket = null
                }

                override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                    Log.w(TAG, "WebSocket connection failed to $url: ${t.message}")
                    isConnectedState = false
                    this@EthernetConnection.webSocket = null
                }
            })

            webSocket = ws

            // Wait up to 1.0 sec for this candidate connection to establish
            var retries = 10
            while (retries-- > 0 && !connectedThisTry) {
                kotlinx.coroutines.delay(100)
            }

            if (connectedThisTry) {
                Log.i(TAG, "Connected to virtual patient monitor at $url")
                return@withContext true
            } else {
                ws.close(1000, "Trying next candidate IP")
                webSocket = null
            }
        }

        Log.e(TAG, "All candidate IP WebSocket connections failed.")
        return@withContext false
    }

    override suspend fun disconnect() = withContext(Dispatchers.IO) {
        try {
            webSocket?.close(1000, "User disconnected")
        } catch (e: Exception) {
            Log.e(TAG, "Error closing websocket", e)
        }
        webSocket = null
        isConnectedState = false
    }

    override suspend fun send(data: ByteArray): Boolean = withContext(Dispatchers.IO) {
        val ws = webSocket ?: return@withContext false
        return@withContext ws.send(String(data))
    }

    override fun observeIncomingData(): Flow<String> = incomingSharedFlow.asSharedFlow()

    override fun isConnected(): Boolean = isConnectedState

    override fun getTransportName(): String = "ETHERNET_WIRED"
}
