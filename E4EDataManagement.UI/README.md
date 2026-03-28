# E4E Data Management — Avalonia UI

A cross-platform desktop GUI for the E4E Data Management tool, built with [Avalonia](https://avaloniaui.net/) and the MVVM pattern. It calls into the same Rust core library as the CLI via a C FFI / P/Invoke bridge.

---

## Requirements

| Dependency | Version |
|------------|---------|
| [.NET SDK](https://dotnet.microsoft.com/download) | 10.0 |
| [Rust toolchain](https://rustup.rs/) | stable |

---

## Building

### Build and run

From the repository root, `dotnet run` automatically builds the Rust native library and copies it next to the output before launching:

```bash
dotnet run --project E4EDataManagement.UI
```

For a release build:

```bash
dotnet publish E4EDataManagement.UI -c Release -r linux-x64 --self-contained
```

The Rust library is built with `--no-default-features` so that PyO3 Python ABI symbols are not included. The produced shared library names are:

| Platform | File |
|----------|------|
| Linux | `lib_core.so` |
| macOS | `lib_core.dylib` |
| Windows | `_core.dll` |

### Building without Rust

Pass `SkipNativeRustBuild=true` to skip the `cargo build` step. Useful when only C# code has changed and a previously built native library is already in place:

```bash
dotnet build E4EDataManagement.UI -p:SkipNativeRustBuild=true
```

---

## Architecture

```
E4EDataManagement.UI/
├── Program.cs                       # Avalonia entry point
├── App.axaml / App.axaml.cs         # Application + FluentTheme
├── Converters.cs                    # AppConverters.BoolToFontWeight
├── ViewModels/
│   ├── ViewModelBase.cs             # ObservableObject base
│   ├── MainWindowViewModel.cs       # Dataset list, commands, execute methods
│   ├── DatasetViewModel.cs          # Per-dataset observable state
│   ├── MissionViewModel.cs          # Per-mission observable state
│   ├── CreateDatasetViewModel.cs    # Form state for New Dataset dialog
│   ├── CreateMissionViewModel.cs    # Form state for New Mission dialog
│   └── AddFilesViewModel.cs         # Form state for Add Files dialog
└── Views/
    ├── MainWindow.axaml             # Main window layout
    ├── MainWindow.axaml.cs          # Code-behind; wires dialog buttons
    ├── CreateDatasetDialog.axaml    # New Dataset modal form
    ├── CreateDatasetDialog.axaml.cs
    ├── CreateMissionDialog.axaml    # New Mission modal form
    ├── CreateMissionDialog.axaml.cs
    ├── AddFilesDialog.axaml         # Add Files modal form
    └── AddFilesDialog.axaml.cs

E4EDataManagement.Native/            # P/Invoke wrapper (referenced by UI)
├── NativeMethods.cs                 # DllImport declarations for e4e_* C API
├── DataManager.cs                   # IDisposable C# wrapper; E4EException
└── Models.cs                        # DatasetInfo / MissionInfo records
```

**Native bridge:** The Rust library exposes a C ABI (`src/ffi.rs`) that the `E4EDataManagement.Native` class library calls via `[DllImport("_core")]`. Complex return values are passed as heap-allocated JSON strings; callers free them with `e4e_string_free`. Errors are reported via `e4e_last_error()` (thread-local, no free required).

---

## Features

### Dataset list (left panel)
- All datasets tracked by the manager
- Bold name on the active dataset; blue dot (●) confirms it
- Green check (✓) on datasets that have been pushed

### Detail pane (right panel)
- Dataset name with **Active** / **Pushed** badges
- Currently active mission name
- Sortable, resizable `DataGrid` of missions showing: name, country, region, site, device, timestamp, staged file count, committed file count
- Validation output panel (appears after Validate is run)

### Toolbar actions

| Button | Enabled when | Action |
|--------|-------------|--------|
| **New Dataset** | Always | Opens a form to create a dataset (date, project, location, directory with folder picker) |
| **New Mission** | A dataset is active | Opens a form to create a mission (timestamp, device, country, region, site, name, notes) |
| **Add Files** | A mission is active | Opens a file picker to stage files into the active mission (with optional destination subfolder and readme flag) |
| **Refresh** | Always | Reload the dataset list and status from disk |
| **Validate** | Always | Run SHA-256 validation on the active dataset; failures appear below the missions grid |
| **Prune** | Always | Remove datasets that have been pushed or are no longer on disk |
| **Push** | Always | Push the active dataset to the typed destination path (runs on a background thread) |

### Status bar
Displays the active dataset/mission name, progress messages, or error details from the last operation.

---

## Configuration

The UI reads and writes state from the same config directory as the CLI:

| Platform | Path |
|----------|------|
| Linux/macOS | `$XDG_CONFIG_HOME/E4EDataManagement/` (defaults to `~/.config/E4EDataManagement/`) |
| Windows | `%LOCALAPPDATA%\Engineers for Exploration\E4EDataManagement\` |

This means datasets initialized via `e4edm` on the command line are immediately visible in the UI, and vice versa.

---

## Development

Open the repository root in an IDE that supports both Rust and C# (VS Code with the C# Dev Kit and rust-analyzer extensions works well).

```bash
# Build Rust native library (no Python ABI)
cargo build --no-default-features

# Build + run the UI (Rust build is triggered automatically by MSBuild)
dotnet run --project E4EDataManagement.UI

# Run C# unit tests (skips Rust build)
dotnet test E4EDataManagement.Tests
```

To add new operations:

1. Add a `pub extern "C"` function to `src/ffi.rs`
2. Add the corresponding `[DllImport]` declaration to `E4EDataManagement.Native/NativeMethods.cs`
3. Expose it through `E4EDataManagement.Native/DataManager.cs`
4. Add an execute method to `MainWindowViewModel.cs`
5. Wire it to a button or dialog in a View / code-behind
