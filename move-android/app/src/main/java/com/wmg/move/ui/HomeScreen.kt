package com.wmg.move.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.wmg.move.R

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onAdd: () -> Unit,
    onEdit: () -> Unit,
    onView: () -> Unit,
) {
    Scaffold(
        topBar = {
            TopAppBar(title = { Text(stringResource(R.string.home_title)) })
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 24.dp, vertical = 24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp, Arrangement.Center),
        ) {
            Button(
                onClick = onAdd,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.home_add))
            }
            Button(
                onClick = onEdit,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.home_edit))
            }
            Button(
                onClick = onView,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.home_view))
            }
        }
    }
}
