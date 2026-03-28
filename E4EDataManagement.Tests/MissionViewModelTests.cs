using E4EDataManagement.Native;
using E4EDataManagement.UI.ViewModels;
using Xunit;

namespace E4EDataManagement.Tests;

public class MissionViewModelTests
{
    [Fact]
    public void Constructor_SetsAllPropertiesFromInfo()
    {
        var info = new MissionInfo(
            Name:           "ED-00 MorningSurvey",
            Path:           "/data/ED-00/MorningSurvey",
            Country:        "US",
            Region:         "Pacific",
            Site:           "North Beach",
            Device:         "reef-laser-01",
            Timestamp:      "2024-03-15T09:00:00-08:00",
            StagedFiles:    3,
            CommittedFiles: 12);

        var vm = new MissionViewModel(info);

        Assert.Equal("ED-00 MorningSurvey",        vm.Name);
        Assert.Equal("US",                          vm.Country);
        Assert.Equal("Pacific",                     vm.Region);
        Assert.Equal("North Beach",                 vm.Site);
        Assert.Equal("reef-laser-01",               vm.Device);
        Assert.Equal("2024-03-15T09:00:00-08:00",  vm.Timestamp);
        Assert.Equal(3,                             vm.StagedFiles);
        Assert.Equal(12,                            vm.CommittedFiles);
    }

    [Fact]
    public void Constructor_ZeroFileCounts()
    {
        var info = new MissionInfo("ED-00 M1", "/p", "US", "CA", "SD",
                                   "dev1", "2024-01-01T00:00:00Z", 0, 0);
        var vm = new MissionViewModel(info);
        Assert.Equal(0, vm.StagedFiles);
        Assert.Equal(0, vm.CommittedFiles);
    }
}
