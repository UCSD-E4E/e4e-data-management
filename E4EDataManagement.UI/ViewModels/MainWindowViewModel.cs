using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using E4EDataManagement.Native;

namespace E4EDataManagement.UI.ViewModels;

public partial class MainWindowViewModel : ViewModelBase
{
    private readonly DataManager _dm;

    [ObservableProperty] private ObservableCollection<DatasetViewModel> _datasets = new();
    [ObservableProperty] private DatasetViewModel? _selectedDataset;
    [ObservableProperty] private string _statusText = "Ready";
    [ObservableProperty] private string _validationOutput = string.Empty;
    [ObservableProperty] private string _pushPath = string.Empty;

    public MainWindowViewModel()
    {
        // Match the path produced by Python's appdirs.AppDirs(
        //   appname="E4EDataManagement", appauthor="Engineers for Exploration"):
        //
        //   Linux/macOS  →  $XDG_CONFIG_HOME/E4EDataManagement
        //                   (~/.config/E4EDataManagement when XDG_CONFIG_HOME is unset)
        //                   appdirs ignores appauthor on non-Windows platforms.
        //
        //   Windows      →  %LOCALAPPDATA%\Engineers for Exploration\E4EDataManagement
        //                   appdirs uses LOCALAPPDATA (non-roaming) by default.
        string configDir;
        if (OperatingSystem.IsWindows())
        {
            configDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "Engineers for Exploration",
                "E4EDataManagement");
        }
        else
        {
            var xdgConfig = Environment.GetEnvironmentVariable("XDG_CONFIG_HOME")
                            ?? Path.Combine(
                                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                                ".config");
            configDir = Path.Combine(xdgConfig, "E4EDataManagement");
        }
        Directory.CreateDirectory(configDir);

        try
        {
            _dm = new DataManager(configDir);
        }
        catch (E4EException ex)
        {
            // Surface the error in the status bar; _dm will remain uninitialized.
            // We throw here so the app can report the problem at startup.
            throw new InvalidOperationException($"Failed to initialize DataManager: {ex.Message}", ex);
        }

        RefreshCommand.Execute(null);
    }

    // ── Commands ─────────────────────────────────────────────────────────────

    /// <summary>Reload the dataset list and status from the native layer.</summary>
    [RelayCommand]
    private void Refresh()
    {
        try
        {
            var infos = _dm.ListDatasets();
            var activeName = _dm.ActiveDataset()?.Name;

            // Update or add dataset view-models
            foreach (var info in infos)
            {
                var isActive = info.Name == activeName;
                var existing = Datasets.FirstOrDefault(d => d.Name == info.Name);
                if (existing != null)
                {
                    existing.Update(info, isActive);
                }
                else
                {
                    Datasets.Add(new DatasetViewModel(info, isActive));
                }
            }

            // Remove datasets that no longer exist
            var toRemove = Datasets
                .Where(d => !infos.Any(i => i.Name == d.Name))
                .ToList();
            foreach (var d in toRemove)
                Datasets.Remove(d);

            // Keep SelectedDataset pointing at the active dataset by default
            if (SelectedDataset == null || !Datasets.Contains(SelectedDataset))
                SelectedDataset = Datasets.FirstOrDefault(d => d.IsActive) ?? Datasets.FirstOrDefault();

            StatusText = _dm.Status();
        }
        catch (E4EException ex)
        {
            StatusText = $"Error refreshing: {ex.Message}";
        }
    }

    /// <summary>Push the active dataset to <see cref="PushPath"/>.</summary>
    [RelayCommand]
    private async Task PushAsync()
    {
        var path = PushPath.Trim();
        if (string.IsNullOrEmpty(path))
        {
            StatusText = "Push path must not be empty.";
            return;
        }

        StatusText = $"Pushing to {path}…";
        try
        {
            await Task.Run(() => _dm.Push(path));
            StatusText = $"Push complete to {path}.";
            Refresh();
        }
        catch (E4EException ex)
        {
            StatusText = $"Push failed: {ex.Message}";
        }
    }

    /// <summary>Validate the active (or selected) dataset and show failures.</summary>
    [RelayCommand]
    private void Validate()
    {
        try
        {
            var failures = _dm.ValidateFailures();
            ValidationOutput = failures.Count == 0
                ? "Validation passed — no failures found."
                : string.Join(Environment.NewLine, failures);
        }
        catch (E4EException ex)
        {
            ValidationOutput = $"Validation error: {ex.Message}";
            StatusText = $"Validation error: {ex.Message}";
        }
    }

    /// <summary>Prune pushed and missing datasets, then refresh.</summary>
    [RelayCommand]
    private void Prune()
    {
        try
        {
            var removed = _dm.Prune();
            StatusText = removed.Count == 0
                ? "Prune complete — nothing to remove."
                : $"Pruned {removed.Count} dataset(s): {string.Join(", ", removed)}.";
            Refresh();
        }
        catch (E4EException ex)
        {
            StatusText = $"Prune failed: {ex.Message}";
        }
    }
}
