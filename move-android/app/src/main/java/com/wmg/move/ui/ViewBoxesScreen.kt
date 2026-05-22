package com.wmg.move.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.wmg.move.R
import com.wmg.move.data.BoxWithItems
import com.wmg.move.viewmodel.ViewBoxesViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ViewBoxesScreen(
    viewModel: ViewBoxesViewModel,
    onBack: () -> Unit,
) {
    val boxes by viewModel.boxes.collectAsState(initial = emptyList())

    // Ephemeral UI state; OK to reset on configuration change.
    var expandedIds by remember { mutableStateOf(setOf<Long>()) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.view_title)) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = stringResource(R.string.content_back),
                        )
                    }
                },
            )
        },
    ) { padding ->
        if (boxes.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    stringResource(R.string.view_empty),
                    modifier = Modifier
                        .padding(24.dp)
                        .alpha(0.6f),
                )
            }
            return@Scaffold
        }

        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            items(boxes, key = { it.box.id }) { row ->
                val isOpen = row.box.id in expandedIds
                BoxRow(
                    row = row,
                    expanded = isOpen,
                    onToggle = {
                        expandedIds = if (isOpen) expandedIds - row.box.id
                        else expandedIds + row.box.id
                    },
                )
                HorizontalDivider()
            }
        }
    }
}

@Composable
private fun BoxRow(
    row: BoxWithItems,
    expanded: Boolean,
    onToggle: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onToggle)
            .padding(horizontal = 16.dp, vertical = 12.dp),
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(row.box.label, style = MaterialTheme.typography.titleMedium)
                Text(
                    text = row.box.room ?: stringResource(R.string.view_no_room),
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.alpha(0.7f),
                )
            }
            Icon(
                imageVector = if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                contentDescription = stringResource(
                    if (expanded) R.string.content_collapse else R.string.content_expand
                ),
            )
        }

        AnimatedVisibility(visible = expanded) {
            Column(
                modifier = Modifier.padding(start = 8.dp, top = 8.dp),
                verticalArrangement = Arrangement.spacedBy(2.dp),
            ) {
                if (row.items.isEmpty()) {
                    Text(
                        stringResource(R.string.view_no_items),
                        modifier = Modifier.alpha(0.6f),
                    )
                } else {
                    row.items.forEach { item ->
                        Text("• ${item.name}")
                    }
                }
            }
        }
    }
}

