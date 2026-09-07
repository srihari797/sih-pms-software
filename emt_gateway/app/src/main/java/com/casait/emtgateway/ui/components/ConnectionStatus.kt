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
import com.casait.emtgateway.domain.model.MonitorConnectionState

@Composable
fun ConnectionStatusCard(
    monitorState: MonitorConnectionState,
    transportName: String,
    patientId: String,
    sessionId: String,
    latencyMs: Long = 0L
) {
    val statusColor = when (monitorState) {
        MonitorConnectionState.MONITORING -> Color(0xFF00E676)
        MonitorConnectionState.CONNECTED -> Color(0xFF00B0FF)
        MonitorConnectionState.CONNECTING -> Color(0xFFFFAB00)
        MonitorConnectionState.DISCONNECTED -> Color(0xFFFF1744)
        MonitorConnectionState.MONITOR_DATA_LOST -> Color(0xFFFF9100)
    }

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
                Text("PATIENT MONITOR", color = Color(0xFF90A4AE), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier.size(10.dp).background(statusColor, shape = CircleShape)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = monitorState.name,
                        color = statusColor,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Text("PATIENT: $patientId", color = Color.White, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                Text("TRANSPORT: $transportName", color = Color(0xFF80D8FF), fontSize = 12.sp)
            }
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Text("SESSION: $sessionId", color = Color(0xFFB0BEC5), fontSize = 11.sp)
                if (latencyMs > 0) {
                    Text("LATENCY: ${latencyMs}ms", color = Color(0xFF00E676), fontSize = 11.sp, fontWeight = FontWeight.Bold)
                }
            }

            if (monitorState == MonitorConnectionState.DISCONNECTED || monitorState == MonitorConnectionState.MONITOR_DATA_LOST) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "⚠️ WARNING: USB/MONITOR DISCONNECTED — RECONNECTING...",
                    color = Color(0xFFFF5252),
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}
