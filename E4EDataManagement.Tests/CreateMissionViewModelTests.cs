using E4EDataManagement.UI.ViewModels;
using Xunit;

namespace E4EDataManagement.Tests;

public class CreateMissionViewModelTests
{
    private static CreateMissionViewModel AllFilled() => new()
    {
        Timestamp = "2024-01-15T10:00:00Z",
        Device = "Raven",
        Country = "USA",
        Region = "California",
        Site = "SD"
    };

    [Fact]
    public void DefaultState_HasTimestamp_OtherRequiredFieldsEmpty()
    {
        var vm = new CreateMissionViewModel();
        Assert.False(string.IsNullOrWhiteSpace(vm.Timestamp));
        Assert.Equal(string.Empty, vm.Device);
        Assert.Equal(string.Empty, vm.Country);
        Assert.Equal(string.Empty, vm.Region);
        Assert.Equal(string.Empty, vm.Site);
    }

    [Fact]
    public void CanConfirm_WhenAllRequiredFieldsFilled_IsTrue()
    {
        Assert.True(AllFilled().CanConfirm);
    }

    [Fact]
    public void CanConfirm_WhenDeviceEmpty_IsFalse()
    {
        var vm = AllFilled();
        vm.Device = "";
        Assert.False(vm.CanConfirm);
    }

    [Fact]
    public void CanConfirm_WhenCountryEmpty_IsFalse()
    {
        var vm = AllFilled();
        vm.Country = "";
        Assert.False(vm.CanConfirm);
    }

    [Fact]
    public void CanConfirm_WhenRegionEmpty_IsFalse()
    {
        var vm = AllFilled();
        vm.Region = "";
        Assert.False(vm.CanConfirm);
    }

    [Fact]
    public void CanConfirm_WhenSiteEmpty_IsFalse()
    {
        var vm = AllFilled();
        vm.Site = "";
        Assert.False(vm.CanConfirm);
    }

    [Fact]
    public void CanConfirm_MissionNameAndNotesAreOptional()
    {
        var vm = AllFilled();
        vm.MissionName = "";
        vm.Notes = "";
        Assert.True(vm.CanConfirm);
    }
}
