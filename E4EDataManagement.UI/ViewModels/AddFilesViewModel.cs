using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace E4EDataManagement.UI.ViewModels;

public partial class AddFilesViewModel : ViewModelBase
{
    public ObservableCollection<string> Files { get; } = new();

    [ObservableProperty]
    private bool _isReadme = false;

    [ObservableProperty]
    private string _destination = string.Empty;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanRemove))]
    private string? _selectedFile;

    public bool CanConfirm => Files.Count > 0;

    public bool CanRemove => SelectedFile != null;

    [RelayCommand]
    private void RemoveSelected()
    {
        if (SelectedFile is not null)
        {
            Files.Remove(SelectedFile);
            OnPropertyChanged(nameof(CanConfirm));
        }
    }

    public void AddFile(string path)
    {
        if (!Files.Contains(path))
        {
            Files.Add(path);
            OnPropertyChanged(nameof(CanConfirm));
        }
    }
}
