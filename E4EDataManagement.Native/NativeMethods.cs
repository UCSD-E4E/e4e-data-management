using System.Runtime.InteropServices;

namespace E4EDataManagement.Native;

/// <summary>
/// Delegate matching the C signature: <c>void (*)(uint64_t current, uint64_t total)</c>.
/// Must be kept alive (via <see cref="GCHandle"/>) for the duration of the native call.
/// </summary>
[UnmanagedFunctionPointer(CallingConvention.Cdecl)]
internal delegate void ProgressCallback(ulong current, ulong total);

/// <summary>
/// P/Invoke declarations for the e4e_* C ABI exported from the Rust _core cdylib.
/// </summary>
internal static class NativeMethods
{
    private const string LibName = "_core";

    // ── Error handling ──────────────────────────────────────────────────────

    /// <summary>
    /// Returns a pointer to the last error string in thread-local storage.
    /// The pointer is valid until the next FFI call on this thread.
    /// Do NOT free this pointer.
    /// </summary>
    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_last_error")]
    internal static extern IntPtr e4e_last_error();

    /// <summary>Helper to read the last error as a managed string.</summary>
    internal static string LastError =>
        Marshal.PtrToStringAnsi(e4e_last_error()) ?? "(unknown error)";

    /// <summary>
    /// Frees a string previously returned via an out-pointer from an e4e_* function.
    /// </summary>
    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_string_free")]
    internal static extern void e4e_string_free(IntPtr s);

    // ── Data manager lifecycle ──────────────────────────────────────────────

    /// <summary>
    /// Loads or creates the data manager state from the given config directory.
    /// Returns a non-null opaque handle on success, IntPtr.Zero on error.
    /// </summary>
    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_dm_load")]
    internal static extern IntPtr e4e_dm_load(
        [MarshalAs(UnmanagedType.LPStr)] string configDir);

    /// <summary>
    /// Frees the data manager handle.
    /// </summary>
    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_dm_free")]
    internal static extern void e4e_dm_free(IntPtr dm);

    // ── Queries ─────────────────────────────────────────────────────────────

    /// <summary>Returns 0 on success, writing the status string to *out.</summary>
    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_status")]
    internal static extern int e4e_status(IntPtr dm, out IntPtr @out);

    /// <summary>Returns 0 on success, writing a JSON array of DatasetInfoJson to *out.</summary>
    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_list_datasets")]
    internal static extern int e4e_list_datasets(IntPtr dm, out IntPtr @out);

    /// <summary>Returns 0 on success, writing a JSON DatasetInfoJson (or "null") to *out.</summary>
    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_active_dataset")]
    internal static extern int e4e_active_dataset(IntPtr dm, out IntPtr @out);

    // ── Mutations ───────────────────────────────────────────────────────────

    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_initialize_dataset")]
    internal static extern int e4e_initialize_dataset(
        IntPtr dm,
        [MarshalAs(UnmanagedType.LPStr)] string date,
        [MarshalAs(UnmanagedType.LPStr)] string project,
        [MarshalAs(UnmanagedType.LPStr)] string location,
        [MarshalAs(UnmanagedType.LPStr)] string directory);

    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_initialize_mission")]
    internal static extern int e4e_initialize_mission(
        IntPtr dm,
        [MarshalAs(UnmanagedType.LPStr)] string timestamp,
        [MarshalAs(UnmanagedType.LPStr)] string device,
        [MarshalAs(UnmanagedType.LPStr)] string country,
        [MarshalAs(UnmanagedType.LPStr)] string region,
        [MarshalAs(UnmanagedType.LPStr)] string site,
        [MarshalAs(UnmanagedType.LPStr)] string missionName,
        [MarshalAs(UnmanagedType.LPStr)] string notes);

    /// <summary>
    /// Activate a dataset and optionally a mission (pass IntPtr.Zero for mission to skip).
    /// </summary>
    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_activate")]
    internal static extern int e4e_activate(
        IntPtr dm,
        [MarshalAs(UnmanagedType.LPStr)] string dataset,
        IntPtr mission);  // nullable *const c_char

    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_add_files")]
    internal static extern int e4e_add_files(
        IntPtr dm,
        [MarshalAs(UnmanagedType.LPStr)] string pathsJson,
        int readme,
        IntPtr destination);  // nullable *const c_char

    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_commit")]
    internal static extern int e4e_commit(IntPtr dm, int readme);

    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_push")]
    internal static extern int e4e_push(
        IntPtr dm,
        [MarshalAs(UnmanagedType.LPStr)] string path);

    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_push_with_progress")]
    internal static extern int e4e_push_with_progress(
        IntPtr dm,
        [MarshalAs(UnmanagedType.LPStr)] string path,
        ProgressCallback? callback);

    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_validate")]
    internal static extern int e4e_validate(IntPtr dm, out IntPtr @out);

    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_validate_with_progress")]
    internal static extern int e4e_validate_with_progress(
        IntPtr dm,
        out IntPtr @out,
        ProgressCallback? callback);

    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_remove_mission")]
    internal static extern int e4e_remove_mission(
        IntPtr dm,
        [MarshalAs(UnmanagedType.LPStr)] string dataset,
        [MarshalAs(UnmanagedType.LPStr)] string mission);

    [DllImport(LibName, CharSet = CharSet.Ansi, EntryPoint = "e4e_prune")]
    internal static extern int e4e_prune(IntPtr dm, out IntPtr @out);
}
