package com.casait.emtgateway.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.casait.emtgateway.domain.model.TransportType

@Composable
fun ConnectionScreen(
    currentTransport: TransportType,
    currentIp: String,
    currentPort: Int,
    onSaveAndConnect: (TransportType, String, Int) -> Unit,
    onBack: () -> Unit
) {
    var selectedTransport by remember { mutableStateOf(currentTransport) }
    var ipText by remember { mutableStateOf(currentIp) }
    var portText by remember { mutableStateOf(currentPort.toString()) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF101418))
            .padding(16.dp)
    ) {
        Text("MONITOR TRANSPORT CONFIGURATION", color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Bold)
        Text("Wired Connection Setup (USB / Ethernet Bridge)", color = Color(0xFF90A4AE), fontSize = 12.sp)

        Spacer(modifier = Modifier.height(20.dp))

        Card(
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF1E2630)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("TRANSPORT METHOD", color = Color(0xFF80D8FF), fontSize = 12.sp, fontWeight = FontWeight.Bold)

                Row(verticalAlignment = Alignment.CenterVertically) {
                    RadioButton(
                        selected = selectedTransport == TransportType.ETHERNET,
                        onClick = { selectedTransport = TransportType.ETHERNET }
                    )
                    Text("Ethernet Bridge (IP Socket / WebSocket)", color = Color.White)
                }

                Row(verticalAlignment = Alignment.CenterVertically) {
                    RadioButton(
                        selected = selectedTransport == TransportType.USB,
                        onClick = { selectedTransport = TransportType.USB }
                    )
                    Text("USB Host Connection (OTG Cable)", color = Color.White)
                }

                Spacer(modifier = Modifier.height(16.dp))

                if (selectedTransport == TransportType.ETHERNET) {
                    OutlinedTextField(
                        value = ipText,
                        onValueChange = { ipText = it },
                        label = { Text("Monitor IP Address") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    Spacer(modifier = Modifier.height(10.dp))
                    OutlinedTextField(
                        value = portText,
                        onValueChange = { portText = it },
                        label = { Text("Port (Default: 8000)") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = {
                val portInt = portText.toIntOrNull() ?: 8000
                val targetIp = if (ipText.isNotBlank()) ipText else "192.168.29.239"
                onSaveAndConnect(selectedTransport, targetIp, portInt)
            },
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF00C853)),
            modifier = Modifier.fillMaxWidth().height(48.dp)
        ) {
            Text("CONNECT TO MONITOR", fontWeight = FontWeight.Bold)
        }

        Spacer(modifier = Modifier.height(12.dp))

        OutlinedButton(
            onClick = onBack,
            modifier = Modifier.fillMaxWidth().height(48.dp)
        ) {
            Text("BACK TO DASHBOARD", color = Color.White)
        }
    }
}
