package com.wmg.move

import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.wmg.move.ui.BoxFormScreen
import com.wmg.move.ui.BoxListScreen
import com.wmg.move.ui.HomeScreen
import com.wmg.move.ui.ViewBoxesScreen
import com.wmg.move.viewmodel.BoxFormViewModel
import com.wmg.move.viewmodel.BoxListViewModel
import com.wmg.move.viewmodel.ViewBoxesViewModel

object Routes {
    const val HOME = "home"
    const val ADD = "add"
    const val EDIT_LIST = "edit_list"
    const val VIEW = "view"
    const val EDIT_FORM = "edit/{boxId}"
    fun editForm(boxId: Long) = "edit/$boxId"
}

@Composable
fun MoveNavHost() {
    val nav = rememberNavController()

    NavHost(navController = nav, startDestination = Routes.HOME) {

        composable(Routes.HOME) {
            HomeScreen(
                onAdd = { nav.navigate(Routes.ADD) },
                onEdit = { nav.navigate(Routes.EDIT_LIST) },
                onView = { nav.navigate(Routes.VIEW) },
            )
        }

        composable(Routes.ADD) {
            val vm: BoxFormViewModel = viewModel(factory = BoxFormViewModel.factory(null))
            BoxFormScreen(
                viewModel = vm,
                onBack = { nav.popBackStack() },
                onFinished = { nav.popBackStack(Routes.HOME, inclusive = false) },
            )
        }

        composable(
            route = Routes.EDIT_FORM,
            arguments = listOf(navArgument("boxId") { type = NavType.LongType }),
        ) { entry ->
            val boxId = entry.arguments?.getLong("boxId")
            val vm: BoxFormViewModel = viewModel(factory = BoxFormViewModel.factory(boxId))
            BoxFormScreen(
                viewModel = vm,
                onBack = { nav.popBackStack() },
                onFinished = { nav.popBackStack(Routes.HOME, inclusive = false) },
            )
        }

        composable(Routes.EDIT_LIST) {
            val vm: BoxListViewModel = viewModel(factory = BoxListViewModel.Factory)
            BoxListScreen(
                viewModel = vm,
                onBack = { nav.popBackStack() },
                onPick = { id -> nav.navigate(Routes.editForm(id)) },
            )
        }

        composable(Routes.VIEW) {
            val vm: ViewBoxesViewModel = viewModel(factory = ViewBoxesViewModel.Factory)
            ViewBoxesScreen(
                viewModel = vm,
                onBack = { nav.popBackStack() },
            )
        }
    }
}
