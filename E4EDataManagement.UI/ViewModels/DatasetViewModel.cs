using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using E4EDataManagement.Native;

namespace E4EDataManagement.UI.ViewModels;

public partial class DatasetViewModel : ViewModelBase
{
    [ObservableProperty] private string _name = string.Empty;
    [ObservableProperty] private bool _isPushed;
    [ObservableProperty] private bool _isActive;
    [ObservableProperty] private string? _activeMission;

    public ObservableCollection<MissionViewModel> Missions { get; } = new();

    public DatasetViewModel(DatasetInfo info, bool isActive)
    {
        _name          = info.Name;
        _isPushed      = info.Pushed;
        _isActive      = isActive;
        _activeMission = info.ActiveMission;

        foreach (var m in info.Missions)
            Missions.Add(new MissionViewModel(m));
    }

    /// <summary>Refreshes all observable properties and mission list from updated info.</summary>
    public void Update(DatasetInfo info, bool isActive)
    {
        Name          = info.Name;
        IsPushed      = info.Pushed;
        IsActive      = isActive;
        ActiveMission = info.ActiveMission;

        // Sync missions: update existing, add new, remove stale
        var infoMissions = info.Missions;

        // Remove missions no longer present
        var toRemove = Missions
            .Where(vm => !infoMissions.Any(m => m.Name == vm.Name))
            .ToList();
        foreach (var vm in toRemove)
            Missions.Remove(vm);

        // Update existing or add new
        for (int i = 0; i < infoMissions.Count; i++)
        {
            var mInfo = infoMissions[i];
            var existing = Missions.FirstOrDefault(vm => vm.Name == mInfo.Name);
            if (existing != null)
            {
                existing.Country        = mInfo.Country;
                existing.Region         = mInfo.Region;
                existing.Site           = mInfo.Site;
                existing.Device         = mInfo.Device;
                existing.Timestamp      = mInfo.Timestamp;
                existing.StagedFiles    = mInfo.StagedFiles;
                existing.CommittedFiles = mInfo.CommittedFiles;
            }
            else
            {
                // Insert at correct position if possible
                if (i <= Missions.Count)
                    Missions.Insert(i, new MissionViewModel(mInfo));
                else
                    Missions.Add(new MissionViewModel(mInfo));
            }
        }
    }
}
