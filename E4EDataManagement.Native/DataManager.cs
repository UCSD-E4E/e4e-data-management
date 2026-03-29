using System.Runtime.InteropServices;
using System.Text.Json;

namespace E4EDataManagement.Native;

/// <summary>
/// Exception thrown when a native E4E operation fails.
/// </summary>
public class E4EException : Exception
{
    public E4EException(string message) : base(message) { }
    public E4EException(string message, Exception inner) : base(message, inner) { }
}

/// <summary>
/// Managed wrapper around the native FfiDataManager handle.
/// Calls are synchronous; run them on a background thread if blocking the UI is a concern.
/// </summary>
public sealed class DataManager : IDisposable
{
    private IntPtr _handle;
    private bool _disposed;

    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    /// <summary>
    /// Opens (or creates) the data manager state from the given config directory.
    /// </summary>
    /// <exception cref="E4EException">Thrown when the native call fails.</exception>
    public DataManager(string configDir)
    {
        _handle = NativeMethods.e4e_dm_load(configDir);
        if (_handle == IntPtr.Zero)
            throw new E4EException($"Failed to load DataManager: {NativeMethods.LastError}");
    }

    // ── Private helpers ──────────────────────────────────────────────────────

    private void ThrowIfDisposed()
    {
        if (_disposed)
            throw new ObjectDisposedException(nameof(DataManager));
    }

    private static void Check(int result)
    {
        if (result != 0)
            throw new E4EException(NativeMethods.LastError);
    }

    /// <summary>
    /// Reads the managed string from a native out-pointer and frees the native memory.
    /// </summary>
    private static string ReadAndFreeString(IntPtr ptr)
    {
        var s = Marshal.PtrToStringAnsi(ptr) ?? string.Empty;
        NativeMethods.e4e_string_free(ptr);
        return s;
    }

    private static T DeserializeOrThrow<T>(string json)
    {
        var result = JsonSerializer.Deserialize<T>(json, JsonOptions);
        if (result is null)
            throw new E4EException($"Failed to deserialize response: {json}");
        return result;
    }

    // ── Public API ───────────────────────────────────────────────────────────

    /// <summary>Returns a human-readable status string for the active dataset/mission.</summary>
    public string Status()
    {
        ThrowIfDisposed();
        Check(NativeMethods.e4e_status(_handle, out IntPtr ptr));
        return ReadAndFreeString(ptr);
    }

    /// <summary>Returns the list of all known datasets.</summary>
    public List<DatasetInfo> ListDatasets()
    {
        ThrowIfDisposed();
        Check(NativeMethods.e4e_list_datasets(_handle, out IntPtr ptr));
        var json = ReadAndFreeString(ptr);
        return DeserializeOrThrow<List<DatasetInfo>>(json);
    }

    /// <summary>Returns the currently active dataset, or null if none.</summary>
    public DatasetInfo? ActiveDataset()
    {
        ThrowIfDisposed();
        Check(NativeMethods.e4e_active_dataset(_handle, out IntPtr ptr));
        var json = ReadAndFreeString(ptr);
        if (json == "null")
            return null;
        return DeserializeOrThrow<DatasetInfo>(json);
    }

    /// <summary>Creates and activates a new dataset.</summary>
    /// <param name="date">ISO date string: YYYY-MM-DD</param>
    /// <param name="project">Project name component</param>
    /// <param name="location">Location name component</param>
    /// <param name="directory">Parent directory in which the dataset folder is created</param>
    public void InitializeDataset(string date, string project, string location, string directory)
    {
        ThrowIfDisposed();
        Check(NativeMethods.e4e_initialize_dataset(_handle, date, project, location, directory));
    }

    /// <summary>Creates and activates a new mission inside the currently active dataset.</summary>
    public void InitializeMission(
        string timestamp,
        string device,
        string country,
        string region,
        string site,
        string missionName,
        string notes)
    {
        ThrowIfDisposed();
        Check(NativeMethods.e4e_initialize_mission(
            _handle, timestamp, device, country, region, site, missionName, notes));
    }

    /// <summary>
    /// Activates a dataset by name and optionally a mission within it.
    /// Pass null for <paramref name="mission"/> to activate only the dataset.
    /// </summary>
    public void Activate(string dataset, string? mission = null)
    {
        ThrowIfDisposed();
        IntPtr missionPtr = IntPtr.Zero;
        GCHandle? gcHandle = null;
        try
        {
            if (mission != null)
            {
                // Marshal the string manually so we can pass a nullable pointer.
                var bytes = System.Text.Encoding.ASCII.GetBytes(mission + '\0');
                gcHandle = GCHandle.Alloc(bytes, GCHandleType.Pinned);
                missionPtr = gcHandle.Value.AddrOfPinnedObject();
            }
            Check(NativeMethods.e4e_activate(_handle, dataset, missionPtr));
        }
        finally
        {
            gcHandle?.Free();
        }
    }

    /// <summary>
    /// Stages files into the active mission (or dataset level when <paramref name="readme"/> is true).
    /// </summary>
    /// <param name="paths">Source file paths to stage.</param>
    /// <param name="readme">When true, stages as dataset-level (README) files.</param>
    /// <param name="destination">Optional sub-directory within the mission for the files.</param>
    public void AddFiles(IEnumerable<string> paths, bool readme, string? destination = null)
    {
        ThrowIfDisposed();
        var pathsJson = JsonSerializer.Serialize(paths.ToList(), JsonOptions);
        IntPtr destPtr = IntPtr.Zero;
        GCHandle? gcHandle = null;
        try
        {
            if (destination != null)
            {
                var bytes = System.Text.Encoding.ASCII.GetBytes(destination + '\0');
                gcHandle = GCHandle.Alloc(bytes, GCHandleType.Pinned);
                destPtr = gcHandle.Value.AddrOfPinnedObject();
            }
            Check(NativeMethods.e4e_add_files(_handle, pathsJson, readme ? 1 : 0, destPtr));
        }
        finally
        {
            gcHandle?.Free();
        }
    }

    /// <summary>Commits staged files.</summary>
    /// <param name="readme">When true, commits dataset-level (README) staged files.</param>
    public void Commit(bool readme)
    {
        ThrowIfDisposed();
        Check(NativeMethods.e4e_commit(_handle, readme ? 1 : 0));
    }

    /// <summary>Pushes the active dataset to the given destination path.</summary>
    public void Push(string path)
    {
        ThrowIfDisposed();
        Check(NativeMethods.e4e_push(_handle, path));
    }

    /// <summary>
    /// Pushes the active dataset to the given destination path, reporting progress via
    /// <paramref name="onProgress"/>.  The callback receives <c>(current, total)</c> file counts.
    /// </summary>
    public void Push(string path, Action<ulong, ulong> onProgress)
    {
        ThrowIfDisposed();
        ProgressCallback cb = (cur, tot) => onProgress(cur, tot);
        var gcHandle = GCHandle.Alloc(cb);
        try
        {
            Check(NativeMethods.e4e_push_with_progress(_handle, path, cb));
        }
        finally
        {
            gcHandle.Free();
        }
    }

    /// <summary>Validates the active dataset and returns a list of failure messages.</summary>
    public List<string> ValidateFailures()
    {
        ThrowIfDisposed();
        Check(NativeMethods.e4e_validate(_handle, out IntPtr ptr));
        var json = ReadAndFreeString(ptr);
        return DeserializeOrThrow<List<string>>(json);
    }

    /// <summary>
    /// Validates the active dataset and returns a list of failure messages, reporting progress
    /// via <paramref name="onProgress"/>.  The callback receives <c>(current, total)</c> file counts.
    /// </summary>
    public List<string> ValidateFailures(Action<ulong, ulong> onProgress)
    {
        ThrowIfDisposed();
        ProgressCallback cb = (cur, tot) => onProgress(cur, tot);
        var gcHandle = GCHandle.Alloc(cb);
        try
        {
            Check(NativeMethods.e4e_validate_with_progress(_handle, out IntPtr ptr, cb));
            var json = ReadAndFreeString(ptr);
            return DeserializeOrThrow<List<string>>(json);
        }
        finally
        {
            gcHandle.Free();
        }
    }

    /// <summary>Removes a mission from the named dataset.</summary>
    public void RemoveMission(string dataset, string mission)
    {
        ThrowIfDisposed();
        Check(NativeMethods.e4e_remove_mission(_handle, dataset, mission));
    }

    /// <summary>
    /// Prunes pushed and missing datasets from the manager.
    /// Returns the list of dataset names that were removed.
    /// </summary>
    public List<string> Prune()
    {
        ThrowIfDisposed();
        Check(NativeMethods.e4e_prune(_handle, out IntPtr ptr));
        var json = ReadAndFreeString(ptr);
        return DeserializeOrThrow<List<string>>(json);
    }

    // ── IDisposable ──────────────────────────────────────────────────────────

    public void Dispose()
    {
        if (!_disposed)
        {
            if (_handle != IntPtr.Zero)
            {
                NativeMethods.e4e_dm_free(_handle);
                _handle = IntPtr.Zero;
            }
            _disposed = true;
        }
    }
}
