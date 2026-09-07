package com.casait.emtgateway.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.casait.emtgateway.domain.model.VitalReading

@Composable
fun VitalSummaryCard(
    vital: VitalReading?,
    latencyMs: Long
) {
    val infiniteTransition = rememberInfiniteTransition()
    val heartAlpha by infiniteTransition.animateFloat(
        initialValue = 0.2f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 600, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        )
    )

    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF161E27)),
        modifier = Modifier.fillMaxWidth().padding(8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "♥",
                        color = Color(0xFFFF1744),
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.alpha(if (vital != null) heartAlpha else 0.3f)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("REAL-TIME VITALS SUMMARY", color = Color(0xFF80CBC4), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
                Text("LATENCY: ${latencyMs} ms", color = Color(0xFFFFD54F), fontSize = 11.sp, fontWeight = FontWeight.Bold)
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                VitalTile("HR", vital?.hr?.toString() ?: "--", "bpm", Color(0xFF00FF41))
                VitalTile("SpO₂", vital?.spo2?.toString() ?: "--", "%", Color(0xFF00F0FF))
                VitalTile("RESP", vital?.rr?.toString() ?: "--", "/min", Color(0xFFFFEE00))
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                val sys = vital?.bp?.sys
                val dia = vital?.bp?.dia
                val bpStr = if (sys != null && dia != null) "$sys/$dia" else "--/--"
                VitalTile("NIBP", bpStr, "mmHg", Color(0xFFFF9900))

                val t1 = vital?.temp?.t1
                val tempStr = if (t1 != null) "$t1 °C" else "--.- °C"
                VitalTile("TEMP", tempStr, "", Color(0xFFFF00EA))
            }
        }
    }
}

@Composable
fun VitalTile(title: String, value: String, unit: String, color: Color) {
    Column {
        Text(title, color = color, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        Row(verticalAlignment = Alignment.Bottom) {
            Text(value, color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold)
            if (unit.isNotEmpty()) {
                Spacer(modifier = Modifier.width(4.dp))
                Text(unit, color = Color(0xFF90A4AE), fontSize = 10.sp)
            }
        }
    }
}
