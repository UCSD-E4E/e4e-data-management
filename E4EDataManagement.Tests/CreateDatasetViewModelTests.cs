using E4EDataManagement.UI.ViewModels;
using Xunit;

namespace E4EDataManagement.Tests;

public class CreateDatasetViewModelTests
{
    [Fact]
    public void DefaultState_HasTodaysDate_OtherFieldsEmpty()
    {
        var vm = new CreateDatasetViewModel();
        Assert.False(string.IsNullOrWhiteSpace(vm.Date));
        Assert.Equal(string.Empty, vm.Project);
        Assert.Equal(string.Empty, vm.Location);
        Assert.Equal(string.Empty, vm.Directory);
    }

    [Fact]
    public void CanConfirm_WhenAllFieldsFilled_IsTrue()
    {
        var vm = new CreateDatasetViewModel
        {
            Date = "2024-01-15",
            Project = "ReefLaser",
            Location = "Palmyra",
            Directory = "/data"
        };
        Assert.True(vm.CanConfirm);
    }

    [Fact]
    public void CanConfirm_WhenProjectEmpty_IsFalse()
    {
        var vm = new CreateDatasetViewModel
        {
            Date = "2024-01-15",
            Project = "",
            Location = "Palmyra",
            Directory = "/data"
        };
        Assert.False(vm.CanConfirm);
    }

    [Fact]
    public void CanConfirm_WhenLocationEmpty_IsFalse()
    {
        var vm = new CreateDatasetViewModel
        {
            Date = "2024-01-15",
            Project = "ReefLaser",
            Location = "",
            Directory = "/data"
        };
        Assert.False(vm.CanConfirm);
    }

    [Fact]
    public void CanConfirm_WhenDirectoryEmpty_IsFalse()
    {
        var vm = new CreateDatasetViewModel
        {
            Date = "2024-01-15",
            Project = "ReefLaser",
            Location = "Palmyra",
            Directory = ""
        };
        Assert.False(vm.CanConfirm);
    }

    [Fact]
    public void CanConfirm_WhenDateWhitespace_IsFalse()
    {
        var vm = new CreateDatasetViewModel
        {
            Date = "   ",
            Project = "ReefLaser",
            Location = "Palmyra",
            Directory = "/data"
        };
        Assert.False(vm.CanConfirm);
    }
}
