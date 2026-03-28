using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Platform.Storage;
using E4EDataManagement.UI.ViewModels;

namespace E4EDataManagement.UI.Views;

public partial class CreateDatasetDialog : Window
{
    public CreateDatasetDialog()
    {
        InitializeComponent();
        DataContext = new CreateDatasetViewModel();

        this.FindControl<Button>("CancelButton")!.Click += (_, _) => Close(null);
        this.FindControl<Button>("OkButton")!.Click += (_, _) => Close((CreateDatasetViewModel)DataContext!);
        this.FindControl<Button>("BrowseButton")!.Click += BrowseButton_Click;
    }

    private async void BrowseButton_Click(object? sender, RoutedEventArgs e)
    {
        var folders = await StorageProvider.OpenFolderPickerAsync(new FolderPickerOpenOptions
        {
            Title = "Select dataset root directory",
            AllowMultiple = false
        });

        if (folders.Count > 0 && DataContext is CreateDatasetViewModel vm)
            vm.Directory = folders[0].Path.LocalPath;
    }
}
