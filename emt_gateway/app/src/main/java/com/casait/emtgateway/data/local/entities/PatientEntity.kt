package com.casait.emtgateway.data.local.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "patients")
data class PatientEntity(
    @PrimaryKey val patientId: String,
    val name: String,
    val age: Int,
    val sex: String,
    val classification: String,
    val createdAt: String
)
