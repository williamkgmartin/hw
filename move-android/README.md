# move-android

Android app for tracking boxes during a house move. Sibling to the `move` CLI
(same data model: a box has a label, an optional room, and a list of items).

## Stack

- Kotlin + Jetpack Compose, Material 3
- Room (SQLite) for persistence
- Navigation-Compose for routing
- minSdk 26, targetSdk 34

## Screens

- **Home** — three buttons: Add Box, Edit Box, View Boxes
- **Add / Edit Box** — same form. Top-right trash icon: deletes the box (with
  confirmation) in Edit mode, or returns to home in Add mode. Items are
  entered as Material 3 input chips (press enter or type a comma to commit).
- **Edit Box list** — pick a box to edit
- **View Boxes** — scrollable list with an expandable items dropdown per row

Every screen except Home has a back arrow in its top app bar.

## Build

Open the `move-android/` directory in Android Studio (Iguana or newer) and
let it sync. Or from the command line:

```sh
./gradlew :app:assembleDebug          # build
./gradlew :app:installDebug           # install on a connected device/emulator
./gradlew :app:connectedAndroidTest   # run the DAO tests on a device/emulator
```

The first build will download the Android SDK components if they're missing
(Android Studio handles this; on the command line you'll need
`local.properties` pointing at an SDK install, e.g. `sdk.dir=/Users/you/Library/Android/sdk`).

## Data location

SQLite DB lives in the app's private storage:
`/data/data/com.wmg.move/databases/move.db`. Uninstall to wipe.

## Tests

DAO tests (Room in-memory DB) live in `app/src/androidTest/`. They cover
create / update / cascade-delete / case-insensitive label uniqueness — the
same data invariants the CLI's pytest suite covers.
