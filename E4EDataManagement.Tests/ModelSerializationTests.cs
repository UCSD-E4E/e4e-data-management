using System.Text.Json;
using E4EDataManagement.Native;
using Xunit;

namespace E4EDataManagement.Tests;

/// <summary>
/// Verifies that DatasetInfo / MissionInfo deserialize correctly from the
/// snake_case JSON that the Rust FFI layer produces.
/// </summary>
public class ModelSerializationTests
{
    // Same options used in DataManager.cs
    private static readonly JsonSerializerOptions Options =
        new(JsonSerializerDefaults.Web);

    // ── MissionInfo ───────────────────────────────────────────────────────────

    [Fact]
    public void MissionInfo_DeserializesAllFields()
    {
        const string json = """
            {
                "name":            "ED-00 Survey",
                "path":            "/data/ED-00/Survey",
                "country":         "US",
                "region":          "CA",
                "site":            "San Diego",
                "device":          "reef-laser-01",
                "timestamp":       "2024-03-15T09:00:00-08:00",
                "staged_files":    2,
                "committed_files": 5
            }
            """;

        var m = JsonSerializer.Deserialize<MissionInfo>(json, Options)!;

        Assert.Equal("ED-00 Survey",             m.Name);
        Assert.Equal("/data/ED-00/Survey",        m.Path);
        Assert.Equal("US",                        m.Country);
        Assert.Equal("CA",                        m.Region);
        Assert.Equal("San Diego",                 m.Site);
        Assert.Equal("reef-laser-01",             m.Device);
        Assert.Equal("2024-03-15T09:00:00-08:00", m.Timestamp);
        Assert.Equal(2,                           m.StagedFiles);
        Assert.Equal(5,                           m.CommittedFiles);
    }

    // ── DatasetInfo ───────────────────────────────────────────────────────────

    [Fact]
    public void DatasetInfo_DeserializesScalarFields()
    {
        const string json = """
            {
                "name":          "2024.03.15.ReefLaser.Palmyra",
                "root":          "/data/2024.03.15.ReefLaser.Palmyra",
                "pushed":        false,
                "last_country":  "US",
                "last_region":   "Pacific",
                "last_site":     "North Beach",
                "missions":      [],
                "active_mission": null
            }
            """;

        var d = JsonSerializer.Deserialize<DatasetInfo>(json, Options)!;

        Assert.Equal("2024.03.15.ReefLaser.Palmyra",        d.Name);
        Assert.Equal("/data/2024.03.15.ReefLaser.Palmyra",  d.Root);
        Assert.False(d.Pushed);
        Assert.Equal("US",           d.LastCountry);
        Assert.Equal("Pacific",      d.LastRegion);
        Assert.Equal("North Beach",  d.LastSite);
        Assert.Empty(d.Missions);
        Assert.Null(d.ActiveMission);
    }

    [Fact]
    public void DatasetInfo_NullableLocationFieldsAcceptNull()
    {
        const string json = """
            {
                "name": "ds", "root": "/ds", "pushed": false,
                "last_country": null, "last_region": null, "last_site": null,
                "missions": [], "active_mission": null
            }
            """;

        var d = JsonSerializer.Deserialize<DatasetInfo>(json, Options)!;

        Assert.Null(d.LastCountry);
        Assert.Null(d.LastRegion);
        Assert.Null(d.LastSite);
        Assert.Null(d.ActiveMission);
    }

    [Fact]
    public void DatasetInfo_DeserializesWithNestedMissions()
    {
        const string json = """
            {
                "name": "2024.01.01.Test.SD", "root": "/data", "pushed": true,
                "last_country": null, "last_region": null, "last_site": null,
                "missions": [
                    {
                        "name": "ED-00 M1", "path": "/data/ED-00/M1",
                        "country": "US", "region": "CA", "site": "SD",
                        "device": "dev1", "timestamp": "2024-01-01T00:00:00Z",
                        "staged_files": 0, "committed_files": 3
                    },
                    {
                        "name": "ED-00 M2", "path": "/data/ED-00/M2",
                        "country": "US", "region": "CA", "site": "SD",
                        "device": "dev2", "timestamp": "2024-01-01T12:00:00Z",
                        "staged_files": 1, "committed_files": 0
                    }
                ],
                "active_mission": "ED-00 M2"
            }
            """;

        var d = JsonSerializer.Deserialize<DatasetInfo>(json, Options)!;

        Assert.True(d.Pushed);
        Assert.Equal(2, d.Missions.Count);
        Assert.Equal("ED-00 M1", d.Missions[0].Name);
        Assert.Equal(3,          d.Missions[0].CommittedFiles);
        Assert.Equal("ED-00 M2", d.Missions[1].Name);
        Assert.Equal(1,          d.Missions[1].StagedFiles);
        Assert.Equal("ED-00 M2", d.ActiveMission);
    }

    [Fact]
    public void DatasetInfo_PushedTrueDeserializesCorrectly()
    {
        const string json = """
            {
                "name": "ds", "root": "/ds", "pushed": true,
                "last_country": null, "last_region": null, "last_site": null,
                "missions": [], "active_mission": null
            }
            """;

        var d = JsonSerializer.Deserialize<DatasetInfo>(json, Options)!;
        Assert.True(d.Pushed);
    }
}
