package com.casait.emtgateway.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.casait.emtgateway.domain.model.InternetState
import com.casait.emtgateway.domain.model.SyncState

@Composable
fun SyncStatusCard(
    internetState: InternetState,
    syncState: SyncState,
    unsyncedCount: Int,
    lastSyncTime: String
) {
    val netColor = if (internetState == InternetState.ONLINE) Color(0xFF00E676) else Color(0xFFFF1744)

    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF1E2630)),
        modifier = Modifier.fillMaxWidth().padding(8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("CLOUD INTERNET PIPELINE", color = Color(0xFF90A4AE), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(10.dp).background(netColor, shape = CircleShape))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = internetState.name,
                        color = netColor,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Column {
                    Text("UNSYNCED ROOM RECORDS", color = Color(0xFFB0BEC5), fontSize = 10.sp)
                    Text(
                        text = "$unsyncedCount",
                        color = if (unsyncedCount > 0) Color(0xFFFFAB00) else Color(0xFF00E676),
                        fontSize = 24.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                Column(horizontalAlignment = Alignment.End) {
                    Text("SYNC STATE", color = Color(0xFFB0BEC5), fontSize = 10.sp)
                    Text(syncState.name, color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(2.dp))
                    Text("LAST: $lastSyncTime", color = Color(0xFF78909C), fontSize = 10.sp)
                }
            }
        }
    }
}
