using E4EDataManagement.Native;
using E4EDataManagement.UI.ViewModels;
using Xunit;

namespace E4EDataManagement.Tests;

public class DatasetViewModelTests
{
    // ── Helpers ───────────────────────────────────────────────────────────────

    private static MissionInfo Mission(string name, int staged = 0, int committed = 0)
        => new(name, $"/data/{name}", "US", "CA", "SD", "dev1",
               "2024-01-01T00:00:00Z", staged, committed);

    private static DatasetInfo Dataset(
        string name = "2024.01.01.Test.SD",
        bool pushed = false,
        string? activeMission = null,
        List<MissionInfo>? missions = null)
        => new(name, $"/data/{name}", pushed,
               LastCountry: null, LastRegion: null, LastSite: null,
               missions ?? [], activeMission);

    // ── Constructor ───────────────────────────────────────────────────────────

    [Fact]
    public void Constructor_SetsNameFromInfo()
    {
        var vm = new DatasetViewModel(Dataset("2024.03.15.ReefLaser.Palmyra"), false);
        Assert.Equal("2024.03.15.ReefLaser.Palmyra", vm.Name);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void Constructor_SetsIsPushedFromInfo(bool pushed)
    {
        var vm = new DatasetViewModel(Dataset(pushed: pushed), false);
        Assert.Equal(pushed, vm.IsPushed);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void Constructor_SetsIsActiveFromParameter(bool isActive)
    {
        var vm = new DatasetViewModel(Dataset(), isActive);
        Assert.Equal(isActive, vm.IsActive);
    }

    [Fact]
    public void Constructor_SetsActiveMissionFromInfo()
    {
        var vm = new DatasetViewModel(Dataset(activeMission: "ED-00 Survey"), false);
        Assert.Equal("ED-00 Survey", vm.ActiveMission);
    }

    [Fact]
    public void Constructor_NullActiveMissionWhenNotSet()
    {
        var vm = new DatasetViewModel(Dataset(), false);
        Assert.Null(vm.ActiveMission);
    }

    [Fact]
    public void Constructor_PopulatesMissionsInOrder()
    {
        var info = Dataset(missions: [Mission("ED-00 M1"), Mission("ED-00 M2")]);
        var vm = new DatasetViewModel(info, false);
        Assert.Equal(2, vm.Missions.Count);
        Assert.Equal("ED-00 M1", vm.Missions[0].Name);
        Assert.Equal("ED-00 M2", vm.Missions[1].Name);
    }

    [Fact]
    public void Constructor_EmptyMissionsWhenNoneProvided()
    {
        var vm = new DatasetViewModel(Dataset(), false);
        Assert.Empty(vm.Missions);
    }

    // ── Update — scalar properties ────────────────────────────────────────────

    [Fact]
    public void Update_ChangesName()
    {
        var vm = new DatasetViewModel(Dataset("old"), false);
        vm.Update(Dataset("new"), false);
        Assert.Equal("new", vm.Name);
    }

    [Fact]
    public void Update_SetsPushedFlag()
    {
        var vm = new DatasetViewModel(Dataset(pushed: false), false);
        vm.Update(Dataset(pushed: true), false);
        Assert.True(vm.IsPushed);
    }

    [Fact]
    public void Update_SetsIsActiveFromParameter()
    {
        var vm = new DatasetViewModel(Dataset(), isActive: false);
        vm.Update(Dataset(), isActive: true);
        Assert.True(vm.IsActive);
    }

    [Fact]
    public void Update_ChangesActiveMission()
    {
        var vm = new DatasetViewModel(Dataset(activeMission: "ED-00 M1"), false);
        vm.Update(Dataset(activeMission: "ED-00 M2"), false);
        Assert.Equal("ED-00 M2", vm.ActiveMission);
    }

    // ── Update — mission collection ───────────────────────────────────────────

    [Fact]
    public void Update_UpdatesExistingMissionInPlace()
    {
        var vm = new DatasetViewModel(Dataset(missions: [Mission("ED-00 M1")]), false);
        var original = vm.Missions[0];

        var updated = new MissionInfo("ED-00 M1", "/data/ED-00 M1",
            "UK", "England", "London", "cam2",
            "2025-06-01T00:00:00Z", StagedFiles: 3, CommittedFiles: 7);
        vm.Update(Dataset(missions: [updated]), false);

        // Same instance — not replaced
        Assert.Same(original, vm.Missions[0]);
        Assert.Equal("UK",      vm.Missions[0].Country);
        Assert.Equal("England", vm.Missions[0].Region);
        Assert.Equal("London",  vm.Missions[0].Site);
        Assert.Equal("cam2",    vm.Missions[0].Device);
        Assert.Equal(3,         vm.Missions[0].StagedFiles);
        Assert.Equal(7,         vm.Missions[0].CommittedFiles);
    }

    [Fact]
    public void Update_AddsNewMission()
    {
        var vm = new DatasetViewModel(Dataset(missions: [Mission("ED-00 M1")]), false);
        vm.Update(Dataset(missions: [Mission("ED-00 M1"), Mission("ED-00 M2")]), false);
        Assert.Equal(2, vm.Missions.Count);
        Assert.Contains(vm.Missions, m => m.Name == "ED-00 M2");
    }

    [Fact]
    public void Update_RemovesStaleMission()
    {
        var vm = new DatasetViewModel(
            Dataset(missions: [Mission("ED-00 M1"), Mission("ED-00 M2")]), false);
        vm.Update(Dataset(missions: [Mission("ED-00 M1")]), false);
        Assert.Single(vm.Missions);
        Assert.Equal("ED-00 M1", vm.Missions[0].Name);
    }

    [Fact]
    public void Update_ClearsMissionsWhenListBecomesEmpty()
    {
        var vm = new DatasetViewModel(
            Dataset(missions: [Mission("ED-00 M1"), Mission("ED-00 M2")]), false);
        vm.Update(Dataset(), false);
        Assert.Empty(vm.Missions);
    }

    [Fact]
    public void Update_InsertsNewMissionAtCorrectIndex()
    {
        // Start: [M1, M2].  Refresh returns [M1, M3, M2].
        // M3 should be inserted between M1 and M2.
        var vm = new DatasetViewModel(
            Dataset(missions: [Mission("ED-00 M1"), Mission("ED-00 M2")]), false);

        vm.Update(Dataset(missions:
            [Mission("ED-00 M1"), Mission("ED-00 M3"), Mission("ED-00 M2")]), false);

        Assert.Equal(3, vm.Missions.Count);
        Assert.Equal("ED-00 M1", vm.Missions[0].Name);
        Assert.Equal("ED-00 M3", vm.Missions[1].Name);
        Assert.Equal("ED-00 M2", vm.Missions[2].Name);
    }

    [Fact]
    public void Update_ReplacesAllMissionsWithDifferentSet()
    {
        var vm = new DatasetViewModel(
            Dataset(missions: [Mission("ED-00 M1"), Mission("ED-00 M2")]), false);
        vm.Update(Dataset(missions: [Mission("ED-01 M1"), Mission("ED-01 M2")]), false);
        Assert.Equal(2, vm.Missions.Count);
        Assert.All(vm.Missions, m => Assert.StartsWith("ED-01", m.Name));
    }
}
