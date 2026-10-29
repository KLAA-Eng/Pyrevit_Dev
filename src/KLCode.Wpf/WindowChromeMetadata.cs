using System.Text.RegularExpressions;

namespace KLCode.Wpf;

/// <summary>Caller-owned identity for the shared shell; no WPF or Revit dependency. Footer destinations and labels are
/// data in lib/GUI/Resources/KLCodeChrome.xaml, read by the shell template; the normalisation vectors in
/// lib/GUI/window_metadata_vectors.json are shared with the Python adapter's tests.</summary>
public sealed class WindowChromeMetadata
{
    public WindowChromeMetadata(string? title, string? version = null)
    {
        Title = (title ?? string.Empty).Trim();
        string candidate = Regex.Replace((version ?? string.Empty).Trim(),
            @"^version\s*[:=]?\s*", string.Empty, RegexOptions.IgnoreCase);
        VersionText = Regex.IsMatch(candidate, @"^[vV]?\d+\.\d+")
            ? "v" + candidate.TrimStart('v', 'V') : string.Empty;
    }

    public string Title { get; }
    public string VersionText { get; }
}
