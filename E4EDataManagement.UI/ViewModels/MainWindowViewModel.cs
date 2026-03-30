using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Threading.Tasks;
using Avalonia.Threading;
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
    [ObservableProperty]
    [NotifyCanExecuteChangedFor(nameof(PushAsyncCommand))]
    private string _pushPath = string.Empty;

    [ObservableProperty]
    [NotifyCanExecuteChangedFor(nameof(PushAsyncCommand))]
    private bool _isOperationRunning;
    [ObservableProperty] private double _operationProgress;
    [ObservableProperty] private string _progressText = string.Empty;

    public MainWindowViewModel()
    {
        var configDir = DataManager.DefaultConfigDir();
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

    // ── Derived state ────────────────────────────────────────────────────────

    /// <summary>True when there is a dataset currently marked active by the data manager.</summary>
    public bool HasActiveDataset => Datasets.Any(d => d.IsActive);

    /// <summary>True when the active dataset has an active mission.</summary>
    public bool HasActiveMission => Datasets.FirstOrDefault(d => d.IsActive)?.ActiveMission != null;

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

            OnPropertyChanged(nameof(HasActiveDataset));
            OnPropertyChanged(nameof(HasActiveMission));
        }
        catch (E4EException ex)
        {
            StatusText = $"Error refreshing: {ex.Message}";
        }
    }

    private bool CanPushAsync() => !string.IsNullOrWhiteSpace(PushPath) && !IsOperationRunning;

    /// <summary>Push the active dataset to <see cref="PushPath"/>.</summary>
    [RelayCommand(CanExecute = nameof(CanPushAsync))]
    private async Task PushAsync()
    {
        var path = PushPath.Trim();
        if (string.IsNullOrEmpty(path))
        {
            StatusText = "Push path must not be empty.";
            return;
        }

        StatusText = $"Pushing to {path}…";
        IsOperationRunning = true;
        OperationProgress = 0;
        ProgressText = string.Empty;
        var sw = Stopwatch.StartNew();
        try
        {
            await Task.Run(() => _dm.Push(path, (current, total) =>
            {
                var elapsed = sw.Elapsed.TotalSeconds;
                var eta = total > 0 && current > 0
                    ? TimeSpan.FromSeconds(elapsed / current * (total - current))
                    : (TimeSpan?)null;
                var etaStr = eta.HasValue ? $"  ETA {eta.Value:mm\\:ss}" : string.Empty;
                Dispatcher.UIThread.Post(() =>
                {
                    OperationProgress = total > 0 ? (double)current / total * 100 : 0;
                    ProgressText = $"Pushing… {current}/{total}{etaStr}";
                });
            }));
            StatusText = $"Push complete to {path}.";
            Refresh();
        }
        catch (E4EException ex)
        {
            StatusText = $"Push failed: {ex.Message}";
        }
        finally
        {
            IsOperationRunning = false;
            OperationProgress = 0;
            ProgressText = string.Empty;
        }
    }

    /// <summary>Validate the active (or selected) dataset and show failures.</summary>
    [RelayCommand]
    private async Task ValidateAsync()
    {
        IsOperationRunning = true;
        OperationProgress = 0;
        ProgressText = string.Empty;
        ValidationOutput = string.Empty;
        var sw = Stopwatch.StartNew();
        try
        {
            var failures = await Task.Run(() => _dm.ValidateFailures((current, total) =>
            {
                var elapsed = sw.Elapsed.TotalSeconds;
                var eta = total > 0 && current > 0
                    ? TimeSpan.FromSeconds(elapsed / current * (total - current))
                    : (TimeSpan?)null;
                var etaStr = eta.HasValue ? $"  ETA {eta.Value:mm\\:ss}" : string.Empty;
                Dispatcher.UIThread.Post(() =>
                {
                    OperationProgress = total > 0 ? (double)current / total * 100 : 0;
                    ProgressText = $"Validating… {current}/{total}{etaStr}";
                });
            }));
            ValidationOutput = failures.Count == 0
                ? "Validation passed — no failures found."
                : string.Join(Environment.NewLine, failures);
        }
        catch (E4EException ex)
        {
            ValidationOutput = $"Validation error: {ex.Message}";
            StatusText = $"Validation error: {ex.Message}";
        }
        finally
        {
            IsOperationRunning = false;
            OperationProgress = 0;
            ProgressText = string.Empty;
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

    // ── Dialog execute methods (called from MainWindow code-behind) ───────────

    /// <summary>Create a new dataset and set it as active.</summary>
    public async Task ExecuteCreateDatasetAsync(
        string date, string project, string location, string directory)
    {
        StatusText = "Creating dataset…";
        try
        {
            await Task.Run(() => _dm.InitializeDataset(date, project, location, directory));
            StatusText = $"Dataset {date}.{project}.{location} created.";
            Refresh();
        }
        catch (E4EException ex)
        {
            StatusText = $"Create dataset failed: {ex.Message}";
        }
    }

    /// <summary>Create a new mission inside the active dataset.</summary>
    public async Task ExecuteCreateMissionAsync(
        string timestamp, string device, string country, string region,
        string site, string missionName, string notes)
    {
        StatusText = "Creating mission…";
        try
        {
            await Task.Run(() =>
                _dm.InitializeMission(timestamp, device, country, region, site, missionName, notes));
            StatusText = "Mission created.";
            Refresh();
        }
        catch (E4EException ex)
        {
            StatusText = $"Create mission failed: {ex.Message}";
        }
    }

    /// <summary>Stage files into the active mission (or dataset level when readme is true).</summary>
    public async Task ExecuteAddFilesAsync(
        IEnumerable<string> paths, bool readme, string? destination)
    {
        StatusText = "Adding files…";
        try
        {
            await Task.Run(() => _dm.AddFiles(paths, readme, destination));
            StatusText = "Files added.";
            Refresh();
        }
        catch (E4EException ex)
        {
            StatusText = $"Add files failed: {ex.Message}";
        }
    }
}
