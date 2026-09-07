package com.casait.emtgateway.data.remote

import kotlinx.coroutines.delay

class MockCloudServer {
    var isCloudOnline: Boolean = true
    var totalUploadedCount: Int = 0

    suspend fun syncPayload(dataType: String, payloadJson: String): Boolean {
        if (!isCloudOnline) return false
        delay(50) // Simulated network transfer time
        totalUploadedCount++
        return true
    }
}
