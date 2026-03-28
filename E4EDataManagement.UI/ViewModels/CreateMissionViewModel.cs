using System;
using CommunityToolkit.Mvvm.ComponentModel;

namespace E4EDataManagement.UI.ViewModels;

public partial class CreateMissionViewModel : ViewModelBase
{
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanConfirm))]
    private string _timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanConfirm))]
    private string _device = string.Empty;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanConfirm))]
    private string _country = string.Empty;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanConfirm))]
    private string _region = string.Empty;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanConfirm))]
    private string _site = string.Empty;

    [ObservableProperty]
    private string _missionName = string.Empty;

    [ObservableProperty]
    private string _notes = string.Empty;

    public bool CanConfirm =>
        !string.IsNullOrWhiteSpace(Timestamp) &&
        !string.IsNullOrWhiteSpace(Device) &&
        !string.IsNullOrWhiteSpace(Country) &&
        !string.IsNullOrWhiteSpace(Region) &&
        !string.IsNullOrWhiteSpace(Site);
}
