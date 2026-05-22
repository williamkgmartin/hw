package com.wmg.move.data

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "boxes",
    indices = [Index(value = ["label"], unique = true)],
)
data class Box(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val label: String,
    val room: String?,
)
