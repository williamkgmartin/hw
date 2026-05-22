package com.wmg.move.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.Companion.APPLICATION_KEY
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.wmg.move.MoveApp
import com.wmg.move.data.BoxSummary
import com.wmg.move.data.MoveDao
import kotlinx.coroutines.flow.Flow

class BoxListViewModel(dao: MoveDao) : ViewModel() {
    val boxes: Flow<List<BoxSummary>> = dao.observeBoxSummaries()

    companion object {
        val Factory: ViewModelProvider.Factory = viewModelFactory {
            initializer {
                val app = this[APPLICATION_KEY] as MoveApp
                BoxListViewModel(app.dao)
            }
        }
    }
}
