package com.casait.emtgateway.data.wired

import kotlinx.coroutines.flow.Flow

interface WiredConnection {
    suspend fun connect(): Boolean
    suspend fun disconnect()
    suspend fun send(data: ByteArray): Boolean
    fun observeIncomingData(): Flow<String>
    fun isConnected(): Boolean
    fun getTransportName(): String
}
