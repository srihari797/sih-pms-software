package com.casait.emtgateway.gateway

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Binder
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat

class GatewayForegroundService : Service() {

    private val binder = LocalBinder()
    lateinit var gatewayManager: GatewayManager

    inner class LocalBinder : Binder() {
        fun getService(): GatewayForegroundService = this@GatewayForegroundService
    }

    override fun onCreate() {
        super.onCreate()
        gatewayManager = GatewayManager(applicationContext)
        startForegroundServiceNotification()
    }

    private fun startForegroundServiceNotification() {
        val channelId = "emt_gateway_channel"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "EMT Gateway Service",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }

        val notification: Notification = NotificationCompat.Builder(this, channelId)
            .setContentTitle("CAS-AIT EMT Gateway Active")
            .setContentText("Receiving patient monitor stream over wired bridge...")
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setOngoing(true)
            .build()

        startForeground(1001, notification)
    }

    override fun onBind(intent: Intent?): IBinder = binder
}
