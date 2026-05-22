package com.wmg.move.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.runtime.collectAsState
import com.wmg.move.R
import com.wmg.move.viewmodel.BoxListViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BoxListScreen(
    viewModel: BoxListViewModel,
    onBack: () -> Unit,
    onPick: (Long) -> Unit,
) {
    val boxes by viewModel.boxes.collectAsState(initial = emptyList())

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.edit_list_title)) },
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
                    stringResource(R.string.edit_list_empty),
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
            items(boxes, key = { it.id }) { box ->
                ListItem(
                    headlineContent = { Text(box.label) },
                    supportingContent = {
                        val sub = box.room?.let { "$it · ${formatItemCount(box.itemCount)}" }
                            ?: formatItemCount(box.itemCount)
                        Text(sub)
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onPick(box.id) },
                )
                HorizontalDivider()
            }
        }
    }
}

private fun formatItemCount(n: Int): String = if (n == 1) "1 item" else "$n items"
