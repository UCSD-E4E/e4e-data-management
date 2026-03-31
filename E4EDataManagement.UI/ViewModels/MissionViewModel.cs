using CommunityToolkit.Mvvm.ComponentModel;
using E4EDataManagement.Native;

namespace E4EDataManagement.UI.ViewModels;

public partial class MissionViewModel : ViewModelBase
{
    [ObservableProperty] private string _name = string.Empty;
    [ObservableProperty] private string _country = string.Empty;
    [ObservableProperty] private string _region = string.Empty;
    [ObservableProperty] private string _site = string.Empty;
    [ObservableProperty] private string _device = string.Empty;
    [ObservableProperty] private string _timestamp = string.Empty;
    [ObservableProperty] private int _stagedFiles;
    [ObservableProperty] private int _committedFiles;

    public MissionViewModel(MissionInfo info)
    {
        _name           = info.Name;
        _country        = info.Country;
        _region         = info.Region;
        _site           = info.Site;
        _device         = info.Device;
        _timestamp      = info.Timestamp;
        _stagedFiles    = info.StagedFiles;
        _committedFiles = info.CommittedFiles;
    }
}
