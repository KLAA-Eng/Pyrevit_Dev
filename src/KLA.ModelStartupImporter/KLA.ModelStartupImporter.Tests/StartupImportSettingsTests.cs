using KLA.ModelStartupImporter.Core;

namespace KLA.ModelStartupImporter.Tests;

public sealed class StartupImportSettingsTests : IDisposable
{
    private readonly string fixtureDirectory = Path.Combine(Path.GetTempPath(), "kla-startup-settings-tests", Guid.NewGuid().ToString("N"));

    [Fact]
    public void Load_ReadsRelativeSeedAndVersionedCatalog()
    {
        Directory.CreateDirectory(fixtureDirectory);
        File.WriteAllText(Path.Combine(fixtureDirectory, "seed.rvt"), "seed fixture");
        File.WriteAllText(Path.Combine(fixtureDirectory, "catalog.json"), """
{
  "version": "2026.08",
  "items": [
    { "itemId": "D-001", "sourceViewName": "Seed Detail", "targetName": "Project Detail", "contentType": "detail" },
    { "itemId": "S-001", "sourceViewName": "Seed Schedule", "targetName": "Project Schedule", "contentType": "schedule" }
  ]
}
""");
        string settingsPath = Path.Combine(fixtureDirectory, "settings.json");
        File.WriteAllText(settingsPath, "{ \"seedModelPath\": \"seed.rvt\", \"catalogPath\": \"catalog.json\" }");

        StartupImportSettings settings = new JsonStartupSettingsProvider().Load(settingsPath);

        Assert.Equal(Path.Combine(fixtureDirectory, "seed.rvt"), settings.SeedModelPath);
        Assert.Equal("2026.08", settings.CatalogVersion);
        Assert.True(settings.Catalog.TryGet("S-001", out CatalogItem? schedule));
        Assert.Equal(StartupItemCategory.Schedule, schedule!.ContentType);
    }

    [Fact]
    public void Load_RejectsCatalogWithoutVersion()
    {
        Directory.CreateDirectory(fixtureDirectory);
        File.WriteAllText(Path.Combine(fixtureDirectory, "seed.rvt"), "seed fixture");
        File.WriteAllText(Path.Combine(fixtureDirectory, "catalog.json"), "{ \"items\": [] }");
        string settingsPath = Path.Combine(fixtureDirectory, "settings.json");
        File.WriteAllText(settingsPath, "{ \"seedModelPath\": \"seed.rvt\", \"catalogPath\": \"catalog.json\" }");

        StartupSettingsException exception = Assert.Throws<StartupSettingsException>(
            () => new JsonStartupSettingsProvider().Load(settingsPath));

        Assert.Contains("version", exception.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void Review_ExcludesKnownExistingMatchesAndBlocksUnknownItems()
    {
        StartupDocumentModel document = TestModels.Document(
            TestModels.Item("D-001", selected: true),
            TestModels.Item("D-002", selected: true),
            TestModels.Item("D-003", selected: false));
        ContentCatalog catalog = new ContentCatalog(new[]
        {
            TestModels.CatalogItem("D-001"),
            TestModels.CatalogItem("D-003"),
        });

        StartupImportReview review = new StartupImportReviewBuilder().Build(document, catalog, new[] { "d-001" });

        Assert.Equal(new[] { "D-001" }, review.ExistingMatches.Select(match => match.Item.ItemId));
        Assert.Empty(review.ActionableMatches);
        Assert.False(review.CanImport);
        Assert.Equal(new[] { "D-002" }, review.Plan.UnknownItems.Select(item => item.ItemId));
    }

    public void Dispose()
    {
        if (Directory.Exists(fixtureDirectory))
        {
            Directory.Delete(fixtureDirectory, recursive: true);
        }
    }
}
