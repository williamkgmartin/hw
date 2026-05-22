package com.wmg.move.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface MoveDao {

    // --- Observed reads ---

    @Transaction
    @Query("SELECT * FROM boxes ORDER BY LOWER(label)")
    fun observeBoxesWithItems(): Flow<List<BoxWithItems>>

    @Query(
        """
        SELECT b.id AS id, b.label AS label, b.room AS room,
               (SELECT COUNT(*) FROM items i WHERE i.box_id = b.id) AS itemCount
        FROM boxes b
        ORDER BY LOWER(b.label)
        """
    )
    fun observeBoxSummaries(): Flow<List<BoxSummary>>

    // --- Point reads ---

    @Transaction
    @Query("SELECT * FROM boxes WHERE id = :id LIMIT 1")
    suspend fun getBoxWithItems(id: Long): BoxWithItems?

    @Query("SELECT * FROM boxes WHERE LOWER(label) = LOWER(:label) LIMIT 1")
    suspend fun findBoxByLabel(label: String): Box?

    // --- Mutations ---

    @Insert
    suspend fun insertBox(box: Box): Long

    @Update
    suspend fun updateBox(box: Box)

    @Insert(onConflict = OnConflictStrategy.ABORT)
    suspend fun insertItems(items: List<Item>)

    @Query("DELETE FROM items WHERE box_id = :boxId")
    suspend fun deleteItemsForBox(boxId: Long)

    @Query("DELETE FROM boxes WHERE id = :id")
    suspend fun deleteBoxById(id: Long)

    // --- Transactional helpers ---

    /**
     * Insert a new box plus its items in one transaction.
     * Throws [DuplicateLabelException] if a box with that label (case-insensitive)
     * already exists.
     */
    @Transaction
    suspend fun createBox(label: String, room: String?, itemNames: List<String>): Long {
        if (findBoxByLabel(label) != null) {
            throw DuplicateLabelException(label)
        }
        val id = insertBox(Box(label = label, room = room))
        if (itemNames.isNotEmpty()) {
            insertItems(itemNames.map { Item(boxId = id, name = it) })
        }
        return id
    }

    /**
     * Replace the items of an existing box and update label/room.
     * Throws [DuplicateLabelException] if the new label collides with a
     * different box.
     */
    @Transaction
    suspend fun updateBoxAndItems(
        id: Long,
        label: String,
        room: String?,
        itemNames: List<String>,
    ) {
        val clash = findBoxByLabel(label)
        if (clash != null && clash.id != id) {
            throw DuplicateLabelException(label)
        }
        updateBox(Box(id = id, label = label, room = room))
        deleteItemsForBox(id)
        if (itemNames.isNotEmpty()) {
            insertItems(itemNames.map { Item(boxId = id, name = it) })
        }
    }
}

class DuplicateLabelException(val label: String) :
    Exception("A box with label '$label' already exists")
