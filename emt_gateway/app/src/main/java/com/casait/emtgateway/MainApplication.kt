package com.casait.emtgateway

import android.app.Application
import com.casait.emtgateway.data.local.AppDatabase

class MainApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        AppDatabase.getDatabase(this)
    }
}
