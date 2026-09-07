package com.casait.emtgateway.gateway

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.hardware.usb.UsbDevice
import android.hardware.usb.UsbManager
import android.util.Log

class UsbDeviceReceiver(
    private val onDeviceAttached: (UsbDevice?) -> Unit,
    private val onDeviceDetached: (UsbDevice?) -> Unit,
    private val onPermissionResult: (UsbDevice?, Boolean) -> Unit
) : BroadcastReceiver() {

    companion object {
        const val ACTION_USB_PERMISSION = "com.casait.emtgateway.USB_PERMISSION"
    }

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action ?: return
        @Suppress("DEPRECATION")
        val device: UsbDevice? = intent.getParcelableExtra(UsbManager.EXTRA_DEVICE)
        Log.i("UsbDeviceReceiver", "USB broadcast received: action=$action, device=${device?.deviceName}")

        when (action) {
            UsbManager.ACTION_USB_DEVICE_ATTACHED -> {
                onDeviceAttached(device)
            }
            UsbManager.ACTION_USB_DEVICE_DETACHED -> {
                onDeviceDetached(device)
            }
            ACTION_USB_PERMISSION -> {
                val granted = intent.getBooleanExtra(UsbManager.EXTRA_PERMISSION_GRANTED, false)
                onPermissionResult(device, granted)
            }
        }
    }
}
