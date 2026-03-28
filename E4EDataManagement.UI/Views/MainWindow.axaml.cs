using Avalonia.Controls;
using E4EDataManagement.UI.ViewModels;

namespace E4EDataManagement.UI.Views;

public partial class MainWindow : Window
{
    private MainWindowViewModel Vm => (MainWindowViewModel)DataContext!;

    public MainWindow()
    {
        InitializeComponent();

        this.FindControl<Button>("NewDatasetButton")!.Click += async (_, _) =>
        {
            var dialog = new CreateDatasetDialog();
            var result = await dialog.ShowDialog<CreateDatasetViewModel?>(this);
            if (result is not null)
                await Vm.ExecuteCreateDatasetAsync(
                    result.Date, result.Project, result.Location, result.Directory);
        };

        this.FindControl<Button>("NewMissionButton")!.Click += async (_, _) =>
        {
            var dialog = new CreateMissionDialog();
            var result = await dialog.ShowDialog<CreateMissionViewModel?>(this);
            if (result is not null)
                await Vm.ExecuteCreateMissionAsync(
                    result.Timestamp, result.Device, result.Country, result.Region,
                    result.Site, result.MissionName, result.Notes);
        };

        this.FindControl<Button>("AddFilesButton")!.Click += async (_, _) =>
        {
            var dialog = new AddFilesDialog();
            var result = await dialog.ShowDialog<AddFilesViewModel?>(this);
            if (result is not null)
                await Vm.ExecuteAddFilesAsync(
                    result.Files,
                    result.IsReadme,
                    string.IsNullOrWhiteSpace(result.Destination) ? null : result.Destination);
        };
    }
}
