using Avalonia.Data.Converters;
using Avalonia.Media;

namespace E4EDataManagement.UI;

public static class AppConverters
{
    /// <summary>Converts a bool to FontWeight: true → Bold, false → Normal.</summary>
    public static FuncValueConverter<bool, FontWeight> BoolToFontWeight { get; } =
        new FuncValueConverter<bool, FontWeight>(b => b ? FontWeight.Bold : FontWeight.Normal);
}
