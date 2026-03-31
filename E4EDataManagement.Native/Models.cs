using System.Text.Json.Serialization;

namespace E4EDataManagement.Native;

/// <summary>
/// Represents a single mission within a dataset as returned by the FFI layer.
/// </summary>
public record MissionInfo(
    [property: JsonPropertyName("name")]            string Name,
    [property: JsonPropertyName("path")]            string Path,
    [property: JsonPropertyName("country")]         string Country,
    [property: JsonPropertyName("region")]          string Region,
    [property: JsonPropertyName("site")]            string Site,
    [property: JsonPropertyName("device")]          string Device,
    [property: JsonPropertyName("timestamp")]       string Timestamp,
    [property: JsonPropertyName("staged_files")]    int StagedFiles,
    [property: JsonPropertyName("committed_files")] int CommittedFiles);

/// <summary>
/// Represents a dataset as returned by the FFI layer.
/// </summary>
public record DatasetInfo(
    [property: JsonPropertyName("name")]          string Name,
    [property: JsonPropertyName("root")]          string Root,
    [property: JsonPropertyName("pushed")]        bool Pushed,
    [property: JsonPropertyName("last_country")]  string? LastCountry,
    [property: JsonPropertyName("last_region")]   string? LastRegion,
    [property: JsonPropertyName("last_site")]     string? LastSite,
    [property: JsonPropertyName("missions")]      List<MissionInfo> Missions,
    [property: JsonPropertyName("active_mission")] string? ActiveMission);
