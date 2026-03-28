using Avalonia.Controls;
using E4EDataManagement.UI.ViewModels;

namespace E4EDataManagement.UI.Views;

public partial class CreateMissionDialog : Window
{
    public CreateMissionDialog()
    {
        InitializeComponent();
        DataContext = new CreateMissionViewModel();

        this.FindControl<Button>("CancelButton")!.Click += (_, _) => Close(null);
        this.FindControl<Button>("OkButton")!.Click += (_, _) => Close((CreateMissionViewModel)DataContext!);
    }
}
