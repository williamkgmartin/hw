package com.wmg.move.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.Companion.APPLICATION_KEY
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.wmg.move.MoveApp
import com.wmg.move.data.DuplicateLabelException
import com.wmg.move.data.MoveDao
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

enum class FormMode { Add, Edit }

enum class SaveError { LabelRequired, LabelTaken }

data class BoxFormState(
    val mode: FormMode = FormMode.Add,
    val boxId: Long? = null,
    val label: String = "",
    val room: String = "",
    val items: List<String> = emptyList(),
    val pendingItem: String = "",
    val loading: Boolean = false,
    val saving: Boolean = false,
    val error: SaveError? = null,
    val saved: Boolean = false,
    val deleted: Boolean = false,
)

class BoxFormViewModel(
    private val dao: MoveDao,
    private val boxId: Long?,
) : ViewModel() {

    private val _state = MutableStateFlow(
        BoxFormState(
            mode = if (boxId == null) FormMode.Add else FormMode.Edit,
            boxId = boxId,
            loading = boxId != null,
        )
    )
    val state: StateFlow<BoxFormState> = _state.asStateFlow()

    init {
        if (boxId != null) {
            viewModelScope.launch {
                val loaded = dao.getBoxWithItems(boxId)
                if (loaded != null) {
                    _state.update {
                        it.copy(
                            loading = false,
                            label = loaded.box.label,
                            room = loaded.box.room.orEmpty(),
                            items = loaded.items.map { i -> i.name },
                        )
                    }
                } else {
                    // Row was deleted underneath us; bounce back.
                    _state.update { it.copy(loading = false, deleted = true) }
                }
            }
        }
    }

    fun onLabelChange(value: String) {
        _state.update { it.copy(label = value, error = null) }
    }

    fun onRoomChange(value: String) {
        _state.update { it.copy(room = value) }
    }

    fun onPendingItemChange(value: String) {
        // Typing a comma commits the current chip.
        if (value.endsWith(",")) {
            commitPendingItem(value.dropLast(1))
        } else {
            _state.update { it.copy(pendingItem = value) }
        }
    }

    fun commitPendingItem(raw: String = _state.value.pendingItem) {
        val trimmed = raw.trim()
        if (trimmed.isEmpty()) {
            _state.update { it.copy(pendingItem = "") }
            return
        }
        _state.update {
            it.copy(items = it.items + trimmed, pendingItem = "")
        }
    }

    fun removeItem(index: Int) {
        _state.update {
            if (index !in it.items.indices) it
            else it.copy(items = it.items.toMutableList().also { list -> list.removeAt(index) })
        }
    }

    fun save() {
        val current = _state.value
        if (current.saving) return

        // Flush any text the user typed but didn't press enter on.
        val pending = current.pendingItem.trim()
        val finalItems = if (pending.isEmpty()) current.items else current.items + pending

        val label = current.label.trim()
        if (label.isEmpty()) {
            _state.update { it.copy(error = SaveError.LabelRequired) }
            return
        }
        val room = current.room.trim().ifEmpty { null }

        _state.update { it.copy(saving = true, error = null, pendingItem = "") }
        viewModelScope.launch {
            try {
                if (current.mode == FormMode.Add) {
                    dao.createBox(label, room, finalItems)
                } else {
                    dao.updateBoxAndItems(current.boxId!!, label, room, finalItems)
                }
                _state.update { it.copy(saving = false, saved = true) }
            } catch (_: DuplicateLabelException) {
                _state.update { it.copy(saving = false, error = SaveError.LabelTaken) }
            }
        }
    }

    fun delete() {
        val id = _state.value.boxId ?: return
        viewModelScope.launch {
            dao.deleteBoxById(id)
            _state.update { it.copy(deleted = true) }
        }
    }

    companion object {
        fun factory(boxId: Long?): ViewModelProvider.Factory = viewModelFactory {
            initializer {
                val app = this[APPLICATION_KEY] as MoveApp
                BoxFormViewModel(app.dao, boxId)
            }
        }
    }
}
