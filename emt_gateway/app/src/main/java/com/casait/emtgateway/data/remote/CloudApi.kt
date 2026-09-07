package com.casait.emtgateway.data.remote

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface CloudApi {
    @POST("/api/v1/cloud/vitals")
    suspend fun uploadVital(@Body payload: String): Response<Unit>

    @POST("/api/v1/cloud/ecg")
    suspend fun uploadEcg(@Body payload: String): Response<Unit>

    @POST("/api/v1/cloud/alarms")
    suspend fun uploadAlarm(@Body payload: String): Response<Unit>

    @POST("/api/v1/cloud/sessions")
    suspend fun uploadSession(@Body payload: String): Response<Unit>
}
