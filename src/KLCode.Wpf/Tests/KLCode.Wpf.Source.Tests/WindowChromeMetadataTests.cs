using System.Text.Json;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace KLCode.Wpf.Source.Tests;

[TestClass]
public sealed class WindowChromeMetadataTests
{
    private static JsonElement Vectors(string family)
    {
        string path = Path.Combine(DesignSystemResourceContractTests.RepositoryRoot(), "lib", "GUI", "window_metadata_vectors.json");
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(path));
        return document.RootElement.GetProperty(family).Clone();
    }

    [TestMethod]
    public void VersionText_MatchesTheSharedVectorsThePythonAdapterIsTestedAgainst()
    {
        foreach (JsonElement vector in Vectors("version").EnumerateArray())
        {
            string? input = vector.GetProperty("input").ValueKind == JsonValueKind.Null ? null : vector.GetProperty("input").GetString();
            Assert.AreEqual(vector.GetProperty("expected").GetString(), new WindowChromeMetadata("Tool", input).VersionText, input ?? "<null>");
        }
    }

    [TestMethod]
    public void Title_IsTrimmedAndNeverInventsAVersion()
    {
        foreach (JsonElement vector in Vectors("title").EnumerateArray())
        {
            string? input = vector.GetProperty("input").ValueKind == JsonValueKind.Null ? null : vector.GetProperty("input").GetString();
            WindowChromeMetadata metadata = new WindowChromeMetadata(input);
            Assert.AreEqual(vector.GetProperty("expected").GetString(), metadata.Title, input ?? "<null>");
            Assert.AreEqual(string.Empty, metadata.VersionText);
        }
    }
}
