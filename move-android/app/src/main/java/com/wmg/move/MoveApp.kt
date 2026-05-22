package com.wmg.move

import android.app.Application
import com.wmg.move.data.MoveDao
import com.wmg.move.data.MoveDatabase

class MoveApp : Application() {
    val dao: MoveDao by lazy { MoveDatabase.get(this).moveDao() }
}
