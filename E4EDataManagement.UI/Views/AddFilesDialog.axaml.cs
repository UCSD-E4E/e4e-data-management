using Avalonia.Controls;
using Avalonia.Platform.Storage;
using E4EDataManagement.UI.ViewModels;

namespace E4EDataManagement.UI.Views;

public partial class AddFilesDialog : Window
{
    public AddFilesDialog()
    {
        InitializeComponent();
        DataContext = new AddFilesViewModel();

        this.FindControl<Button>("CancelButton")!.Click += (_, _) => Close(null);
        this.FindControl<Button>("OkButton")!.Click += (_, _) => Close((AddFilesViewModel)DataContext!);
        this.FindControl<Button>("AddFilesButton")!.Click += AddFilesButton_Click;
    }

    private async void AddFilesButton_Click(object? sender, System.EventArgs e)
    {
        var files = await StorageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
        {
            Title = "Select files to add",
            AllowMultiple = true
        });

        if (DataContext is AddFilesViewModel vm)
        {
            foreach (var file in files)
                vm.AddFile(file.Path.LocalPath);
        }
    }
}
