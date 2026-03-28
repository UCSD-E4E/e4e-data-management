# E4E Data Management — Avalonia UI

A cross-platform desktop GUI for the E4E Data Management tool, built with [Avalonia](https://avaloniaui.net/) and the MVVM pattern. It calls into the same Rust core library as the CLI via a C FFI / P/Invoke bridge.

---

## Requirements

| Dependency | Version |
|------------|---------|
| [.NET SDK](https://dotnet.microsoft.com/download) | 8.0 or later |
| [Rust toolchain](https://rustup.rs/) | stable |

---

## Building

### 1. Build the Rust native library

From the repository root:

```bash
cargo build --release
```

This produces the shared library that the UI P/Invokes into:

| Platform | Output file |
|----------|------------|
| Linux | `target/release/lib_core.so` |
| macOS | `target/release/lib_core.dylib` |
| Windows | `target/release/_core.dll` |

### 2. Build and run the UI

```bash
cd E4EDataManagement.UI
dotnet run
```

`dotnet run` uses the `Debug` profile by default. For a release build:

```bash
dotnet publish -c Release -r linux-x64 --self-contained
```

### 3. Placing the native library

The UI resolves `_core` via the standard .NET native library search path. The simplest approach is to copy the built library next to the UI binary:

```bash
# Debug run (library next to the project)
cp ../target/debug/lib_core.so .

# Published output
cp ../target/release/lib_core.so bin/Release/net8.0/linux-x64/publish/
```

On macOS replace `lib_core.so` with `lib_core.dylib`; on Windows use `_core.dll`.

---

## Architecture

```
E4EDataManagement.UI/
├── Program.cs                   # Avalonia entry point
├── App.axaml / App.axaml.cs     # Application + FluentTheme
├── ViewModels/
│   ├── ViewModelBase.cs         # ObservableObject base
│   ├── MainWindowViewModel.cs   # Root VM: dataset list, commands
│   ├── DatasetViewModel.cs      # Per-dataset state
│   └── MissionViewModel.cs      # Per-mission state
└── Views/
    ├── MainWindow.axaml         # Main window layout
    └── MainWindow.axaml.cs      # Code-behind

E4EDataManagement.Native/        # P/Invoke wrapper (referenced by UI)
├── NativeMethods.cs             # DllImport declarations for e4e_* C API
├── DataManager.cs               # IDisposable C# wrapper; E4EException
└── Models.cs                    # DatasetInfo / MissionInfo records
```

**Native bridge:** The Rust library exposes a C ABI (`src/ffi.rs`) that the `E4EDataManagement.Native` class library calls via `[DllImport("_core")]`. Complex return values are passed as heap-allocated JSON strings; callers free them with `e4e_string_free`. Errors are reported via `e4e_last_error()` (thread-local, no free required).

---

## Features

### Dataset list (left panel)
- All datasets tracked by the manager
- Blue dot (●) on the active dataset
- Green check (✓) on datasets that have been pushed

### Detail pane (right panel)
- Dataset name with **Active** / **Pushed** badges
- Currently active mission name
- Sortable, resizable `DataGrid` of missions showing: name, country, region, site, device, timestamp, staged file count, committed file count

### Toolbar actions

| Button | Action |
|--------|--------|
| **Refresh** | Reload the dataset list and status from disk |
| **Validate** | Run SHA-256 validation on the active dataset; failures appear in the validation panel |
| **Prune** | Remove datasets that have been pushed or are no longer on disk |
| **Push** | Push the active dataset to the typed destination path (runs on a background thread) |

### Status bar
Displays the active dataset/mission name, or error messages from the last operation.

---

## Configuration

The UI reads and writes state from the same config directory as the CLI:

| Platform | Path |
|----------|------|
| Linux/macOS | `~/.config/Engineers for Exploration/E4EDataManagement/` |
| Windows | `%APPDATA%\Engineers for Exploration\E4EDataManagement\` |

This means datasets initialized via `e4edm` on the command line are immediately visible in the UI, and vice versa.

---

## Development

Open the repository root in an IDE that supports both Rust and C# (VS Code with the C# Dev Kit and rust-analyzer extensions works well).

```bash
# Rebuild the Rust extension after changes to src/
cargo build

# Run the UI against the debug library
cp target/debug/lib_core.so E4EDataManagement.UI/
cd E4EDataManagement.UI && dotnet run
```

To add new operations:

1. Add a `pub extern "C"` function to `src/ffi.rs`
2. Add the corresponding `[DllImport]` declaration to `E4EDataManagement.Native/NativeMethods.cs`
3. Expose it through `E4EDataManagement.Native/DataManager.cs`
4. Wire it to a `[RelayCommand]` in the appropriate ViewModel
