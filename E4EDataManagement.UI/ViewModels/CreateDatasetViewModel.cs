using System;
using CommunityToolkit.Mvvm.ComponentModel;

namespace E4EDataManagement.UI.ViewModels;

public partial class CreateDatasetViewModel : ViewModelBase
{
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanConfirm))]
    private string _date = DateTime.Today.ToString("yyyy-MM-dd");

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanConfirm))]
    private string _project = string.Empty;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanConfirm))]
    private string _location = string.Empty;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanConfirm))]
    private string _directory = string.Empty;

    public bool CanConfirm =>
        !string.IsNullOrWhiteSpace(Date) &&
        !string.IsNullOrWhiteSpace(Project) &&
        !string.IsNullOrWhiteSpace(Location) &&
        !string.IsNullOrWhiteSpace(Directory);
}
