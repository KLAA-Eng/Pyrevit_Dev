using System;
using System.Text.RegularExpressions;

namespace KLCode.Wpf;

/// <summary>Caller-owned identity for the shared shell; no WPF or Revit dependency.</summary>
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
    public Uri PrototypeUri { get; } = new Uri("https://forms.cloud.microsoft/r/HjuggSZqyU");
    public Uri OutreachUri { get; } = new Uri("https://forms.microsoft.com/Pages/ResponsePage.aspx?id=Bfmd9K3MFkqVWdMqprbPvvfxx29Ur-NGhLTDKxuFAqVUMU1OMUpRWDRKUDBMNEFEMlQ2SEJJNFdCUi4u");
}
