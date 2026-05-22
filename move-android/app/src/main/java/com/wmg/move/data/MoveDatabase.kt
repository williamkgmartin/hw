package com.wmg.move.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [Box::class, Item::class],
    version = 1,
    exportSchema = false,
)
abstract class MoveDatabase : RoomDatabase() {
    abstract fun moveDao(): MoveDao

    companion object {
        @Volatile private var instance: MoveDatabase? = null

        fun get(context: Context): MoveDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    MoveDatabase::class.java,
                    "move.db",
                ).build().also { instance = it }
            }
    }
}
