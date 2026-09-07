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
import com.casait.emtgateway.domain.model.CaseStatus
import com.casait.emtgateway.domain.model.GatewayState
import com.casait.emtgateway.domain.model.VitalReading
import com.casait.emtgateway.ui.components.ConnectionStatusCard
import com.casait.emtgateway.ui.components.SyncStatusCard
import com.casait.emtgateway.ui.components.VitalSummaryCard

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GatewayScreen(
    state: GatewayState,
    vital: VitalReading?,
    onNewCaseClick: () -> Unit,
    onStartCaseClick: (name: String, age: Int, sex: String, classification: String, esiLevel: Int) -> Unit,
    onCloseCaseClick: () -> Unit,
    onToggleInternet: () -> Unit
) {
    var nameInput by remember { mutableStateOf("Raj Kumar") }
    var ageInput by remember { mutableStateOf("42") }
    var sexInput by remember { mutableStateOf("Male") }
    var classInput by remember { mutableStateOf("Adult") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF101418))
            .padding(12.dp)
    ) {
        // TOP APP BAR
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
            modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
        ) {
            Column {
                Text("CAS-AIT EMT GATEWAY", color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                Text("AMBULANCE EDGE DATA BRIDGE", color = Color(0xFF00B0FF), fontSize = 11.sp)
            }
            Text("PHASE 2", color = Color(0xFFFFD54F), fontSize = 11.sp, fontWeight = FontWeight.Bold)
        }

        Spacer(modifier = Modifier.height(6.dp))

        when (state.caseStatus) {
            CaseStatus.NO_ACTIVE_CASE, CaseStatus.CASE_CLOSED -> {
                Card(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF1E2630))
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "NO ACTIVE CASE",
                            color = Color(0xFFFF5252),
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Monitor Connection: NOT CONNECTED / STANDBY",
                            color = Color(0xFF90A4AE),
                            fontSize = 12.sp
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(
                            onClick = onNewCaseClick,
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0088FF)),
                            modifier = Modifier.fillMaxWidth().height(48.dp)
                        ) {
                            Text("NEW CASE", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        }
                    }
                }
            }

            CaseStatus.CREATING_CASE -> {
                Card(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF1E2630))
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("NEW CASE ENTRY", color = Color(0xFF00B0FF), fontSize = 16.sp, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(12.dp))

                        OutlinedTextField(
                            value = nameInput,
                            onValueChange = { nameInput = it },
                            label = { Text("Patient Name") },
                            modifier = Modifier.fillMaxWidth(),
                            colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = Color(0xFF00B0FF))
                        )
                        Spacer(modifier = Modifier.height(8.dp))

                        OutlinedTextField(
                            value = ageInput,
                            onValueChange = { ageInput = it },
                            label = { Text("Age") },
                            modifier = Modifier.fillMaxWidth(),
                            colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = Color(0xFF00B0FF))
                        )
                        Spacer(modifier = Modifier.height(8.dp))

                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton(
                                onClick = { sexInput = if (sexInput == "Male") "Female" else "Male" },
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("Sex: $sexInput", color = Color.White)
                            }

                            OutlinedButton(
                                onClick = {
                                    classInput = when (classInput) {
                                        "Adult" -> "Pediatric"
                                        "Pediatric" -> "Neonate"
                                        else -> "Adult"
                                    }
                                },
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("Class: $classInput", color = Color.White)
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "ESI Triage: AUTOMATIC (Calculated dynamically from live vitals)",
                            color = Color(0xFF00B0FF),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        Button(
                            onClick = {
                                val parsedAge = ageInput.toIntOrNull() ?: 0
                                onStartCaseClick(nameInput, parsedAge, sexInput, classInput, 3)
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2E7D32)),
                            modifier = Modifier.fillMaxWidth().height(48.dp)
                        ) {
                            Text("START CASE", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        }
                    }
                }
            }

            CaseStatus.MONITORING_ACTIVE -> {
                // ACTIVE CASE HEADER CARD
                Card(
                    modifier = Modifier.fillMaxWidth().padding(bottom = 6.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF1B2E24))
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("ACTIVE CASE: ${state.activeCaseId}", color = Color(0xFF00FF66), fontWeight = FontWeight.Bold, fontSize = 14.sp)
                            Surface(
                                color = when (state.activeEsiLevel) {
                                    1 -> Color(0xFFFF1744)
                                    2 -> Color(0xFFFF9100)
                                    3 -> Color(0xFFFFD54F)
                                    4 -> Color(0xFF00E676)
                                    else -> Color(0xFF00B0FF)
                                },
                                shape = RoundedCornerShape(4.dp)
                            ) {
                                Text(
                                    text = "ESI LEVEL ${state.activeEsiLevel}",
                                    color = Color.Black,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text("Patient: ${state.activePatientName} (${state.activeAge} y/o, ${state.activeSex}, ${state.activeClassification})", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                    }
                }

                // AUTOMATIC ESI TRIAGE CARD
                Card(
                    modifier = Modifier.fillMaxWidth().padding(bottom = 6.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF1E2630))
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Row(
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text("ESI LEVEL — AUTO GENERATED", color = Color(0xFF90A4AE), fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            Text(
                                text = "ESI ${state.activeEsiLevel}",
                                color = when (state.activeEsiLevel) {
                                    1 -> Color(0xFFFF1744)
                                    2 -> Color(0xFFFF9100)
                                    3 -> Color(0xFFFFD54F)
                                    4 -> Color(0xFF00E676)
                                    else -> Color(0xFF00B0FF)
                                },
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text("Reason: ${state.activeEsiReason}", color = Color.White, fontSize = 12.sp)
                        Spacer(modifier = Modifier.height(2.dp))
                        Text("Source: AUTOMATIC TRIAGE ENGINE", color = Color(0xFF00B0FF), fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    }
                }

                // MONITOR CONNECTION & VITALS READOUT
                ConnectionStatusCard(
                    monitorState = state.monitorState,
                    transportName = state.transportType.name,
                    patientId = state.activeCaseId,
                    sessionId = state.activeSessionId,
                    latencyMs = state.currentLatencyMs
                )

                VitalSummaryCard(
                    vital = vital,
                    latencyMs = state.currentLatencyMs
                )

                Spacer(modifier = Modifier.height(8.dp))

                Button(
                    onClick = onCloseCaseClick,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFC62828)),
                    modifier = Modifier.fillMaxWidth().height(44.dp)
                ) {
                    Text("CLOSE CASE", fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Color.White)
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // SYNC PIPELINE & ROOM BUFFER CARD
        SyncStatusCard(
            internetState = state.internetState,
            syncState = state.syncState,
            unsyncedCount = state.unsyncedRecordCount,
            lastSyncTime = state.lastSyncTimestamp
        )

        Spacer(modifier = Modifier.weight(1f))

        // INTERNET TOGGLE DEMO BUTTON
        Button(
            onClick = onToggleInternet,
            colors = ButtonDefaults.buttonColors(
                containerColor = if (state.internetState.name == "ONLINE") Color(0xFF455A64) else Color(0xFF2E7D32)
            ),
            modifier = Modifier.fillMaxWidth().height(42.dp)
        ) {
            Text(
                text = if (state.internetState.name == "ONLINE") "SIMULATE INTERNET DISCONNECT (OFFLINE)" else "RESTORE INTERNET CONNECTIVITY (ONLINE)",
                fontWeight = FontWeight.Bold,
                fontSize = 11.sp
            )
        }
    }
}
