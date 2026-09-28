using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using KLCode.FamilyStudio.Core.Search;
using KLCode.FamilyStudio.Database.Repositories;
using KLCode.FamilyStudio.Indexer;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace KLCode.FamilyStudio.Core.Tests;

[TestClass]
public sealed class IndexerCliTests
{
    [TestMethod]
    public async Task Main_IndexesFilesystemMetadataIntoConfiguredDatabase()
    {
        using TempDirectory temp = new TempDirectory();
        string root = temp.CreateDirectory("library");
        temp.WriteFile("library/Desk.rfa", "fixture");
        string databasePath = Path.Combine(temp.Path, "cache", "families.sqlite");
        string configurationPath = WriteConfiguration(temp, root, databasePath);

        int exitCode = await Program.Main(new[] { "--config", configurationPath });

        Assert.AreEqual(0, exitCode);
        using SqliteFamilyRepository repository = new SqliteFamilyRepository(databasePath);
        IReadOnlyList<FamilySearchResult> results = repository.Search(
            new FamilySearchQuery("Desk", null, "Draft", null, 10));
        Assert.AreEqual(1, results.Count);
        Assert.AreEqual(Path.Combine(root, "Desk.rfa"), results[0].FilePath);
    }

    [TestMethod]
    public async Task Main_RejectsInvalidArgumentsAndMissingConfiguration()
    {
        Assert.AreEqual(2, await Program.Main(Array.Empty<string>()));
        Assert.AreEqual(2, await Program.Main(new[] { "--config", "/missing/config.json" }));
    }

    [TestMethod]
    public async Task FilesystemAdapters_ValidateMissingFilesAndHonorCancellation()
    {
        FileSystemMetadataExtractor extractor = new FileSystemMetadataExtractor();
        NoThumbnailService thumbnails = new NoThumbnailService();
        using CancellationTokenSource cancellation = new CancellationTokenSource();
        cancellation.Cancel();

        await Assert.ThrowsExactlyAsync<FileNotFoundException>(
            () => extractor.ExtractAsync("/missing/family.rfa", CancellationToken.None));
        await Assert.ThrowsExactlyAsync<OperationCanceledException>(
            () => thumbnails.EnsureThumbnailAsync(null!, "/thumbs", cancellation.Token));
    }

    private static string WriteConfiguration(TempDirectory temp, string root, string databasePath)
    {
        string configurationPath = Path.Combine(temp.Path, "family-studio.json");
        string json = JsonSerializer.Serialize(new
        {
            libraryRoots = new[] { new { path = root, enabled = true, defaultStatus = "Draft" } },
            databasePath,
            thumbnailDirectory = Path.Combine(temp.Path, "thumbnails"),
        });
        File.WriteAllText(configurationPath, json);
        return configurationPath;
    }
}
