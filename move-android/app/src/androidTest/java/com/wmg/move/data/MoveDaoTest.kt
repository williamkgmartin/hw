package com.wmg.move.data

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MoveDaoTest {

    private lateinit var db: MoveDatabase
    private lateinit var dao: MoveDao

    @Before
    fun setUp() {
        val ctx = ApplicationProvider.getApplicationContext<android.content.Context>()
        db = Room.inMemoryDatabaseBuilder(ctx, MoveDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        dao = db.moveDao()
    }

    @After
    fun tearDown() {
        db.close()
    }

    @Test
    fun createBox_persistsLabelRoomAndItems() = runTest {
        val id = dao.createBox("11", "kitchen", listOf("knife", "book"))
        val loaded = dao.getBoxWithItems(id)
        assertNotNull(loaded)
        assertEquals("11", loaded!!.box.label)
        assertEquals("kitchen", loaded.box.room)
        assertEquals(listOf("knife", "book"), loaded.items.map { it.name })
    }

    @Test
    fun createBox_rejectsDuplicateLabel_caseInsensitive() = runTest {
        dao.createBox("Box-A", null, emptyList())
        var threw = false
        try {
            dao.createBox("box-a", null, emptyList())
        } catch (_: DuplicateLabelException) {
            threw = true
        }
        assertTrue(threw)
    }

    @Test
    fun updateBoxAndItems_replacesItems() = runTest {
        val id = dao.createBox("11", null, listOf("knife", "book"))
        dao.updateBoxAndItems(id, "11", "kitchen", listOf("fork", "spoon", "chair"))
        val loaded = dao.getBoxWithItems(id)!!
        assertEquals("kitchen", loaded.box.room)
        assertEquals(listOf("fork", "spoon", "chair"), loaded.items.map { it.name })
    }

    @Test
    fun deleteBox_cascadesItems() = runTest {
        val id = dao.createBox("11", null, listOf("a", "b", "c"))
        dao.deleteBoxById(id)
        assertNull(dao.getBoxWithItems(id))
        // Summary should also be empty.
        val summaries = dao.observeBoxSummaries().first()
        assertTrue(summaries.isEmpty())
    }

    @Test
    fun observeBoxSummaries_reportsCountsAndOrdering() = runTest {
        dao.createBox("b", null, listOf("x"))
        dao.createBox("a", null, listOf("x", "y"))
        dao.createBox("C", null, emptyList())
        val rows = dao.observeBoxSummaries().first()
        assertEquals(listOf("a", "b", "C"), rows.map { it.label })
        assertEquals(listOf(2, 1, 0), rows.map { it.itemCount })
    }

    @Test
    fun updateBoxAndItems_rejectsLabelOwnedByAnotherBox() = runTest {
        val a = dao.createBox("11", null, emptyList())
        dao.createBox("12", null, emptyList())
        var threw = false
        try {
            dao.updateBoxAndItems(a, "12", null, emptyList())
        } catch (_: DuplicateLabelException) {
            threw = true
        }
        assertTrue(threw)
    }
}
