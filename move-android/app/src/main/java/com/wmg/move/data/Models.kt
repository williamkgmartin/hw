package com.wmg.move.data

import androidx.room.Embedded
import androidx.room.Relation

data class BoxWithItems(
    @Embedded val box: Box,
    @Relation(
        parentColumn = "id",
        entityColumn = "box_id",
    )
    val items: List<Item>,
)

data class BoxSummary(
    val id: Long,
    val label: String,
    val room: String?,
    val itemCount: Int,
)
