package com.casait.emtgateway.gateway

import com.casait.emtgateway.data.local.SyncQueueDao
import com.casait.emtgateway.data.remote.MockCloudServer
import com.casait.emtgateway.domain.model.InternetState
import com.casait.emtgateway.domain.model.SyncState
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.Instant

class SyncManager(
    private val syncQueueDao: SyncQueueDao,
    private val cloudServer: MockCloudServer = MockCloudServer()
) {
    private val scope = CoroutineScope(Dispatchers.IO)

    private val _internetState = MutableStateFlow(InternetState.OFFLINE)
    val internetState: StateFlow<InternetState> = _internetState.asStateFlow()

    private val _syncState = MutableStateFlow(SyncState.IDLE)
    val syncState: StateFlow<SyncState> = _syncState.asStateFlow()

    private val _lastSyncTime = MutableStateFlow("NEVER")
    val lastSyncTime: StateFlow<String> = _lastSyncTime.asStateFlow()

    init {
        startSyncWorker()
    }

    fun setInternetState(online: Boolean) {
        _internetState.value = if (online) InternetState.ONLINE else InternetState.OFFLINE
        cloudServer.isCloudOnline = online
        if (!online) {
            _syncState.value = SyncState.PAUSED_OFFLINE
        }
    }

    private fun startSyncWorker() {
        scope.launch {
            while (true) {
                delay(1000)
                if (_internetState.value == InternetState.ONLINE) {
                    processPendingQueue()
                }
            }
        }
    }

    private suspend fun processPendingQueue() {
        val pendingItems = syncQueueDao.getPendingItems(limit = 10)
        if (pendingItems.isEmpty()) {
            if (_syncState.value != SyncState.PAUSED_OFFLINE) {
                _syncState.value = SyncState.IDLE
            }
            return
        }

        _syncState.value = SyncState.SYNCING

        for (item in pendingItems) {
            if (_internetState.value == InternetState.OFFLINE) break

            syncQueueDao.updateStatus(item.id, "SENDING", Instant.now().toString())

            val success = cloudServer.syncPayload(item.dataType, item.payloadJson)
            if (success) {
                syncQueueDao.updateStatus(item.id, "SYNCED", Instant.now().toString(), null)
                _lastSyncTime.value = Instant.now().toString()
            } else {
                syncQueueDao.updateStatus(item.id, "FAILED", Instant.now().toString(), "Cloud endpoint unreachable or offline")
                delay(1000) // Controlled backoff retry delay
            }
        }

        syncQueueDao.purgeSynced()
    }
}
