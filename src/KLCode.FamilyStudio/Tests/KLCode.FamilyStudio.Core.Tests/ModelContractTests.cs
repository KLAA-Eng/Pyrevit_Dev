using System;
using System.IO;
using KLCode.FamilyStudio.Core.Configuration;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;
using KLCode.FamilyStudio.Core.Search;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace KLCode.FamilyStudio.Core.Tests;

[TestClass]
public sealed class ModelContractTests
{
    [TestMethod]
    public void ImmutableModels_ExposeTheValidatedValuesPassedAtTheirBoundaries()
    {
        DateTimeOffset timestamp = new DateTimeOffset(2026, 8, 26, 12, 0, 0, TimeSpan.Zero);
        LibraryRoot root = new LibraryRoot("/library", true, "Architecture", "Draft");
        LibraryConfiguration config = new LibraryConfiguration(new[] { root }, "/db", "/thumbs");
        LibraryFileCandidate file = new LibraryFileCandidate("/library/Desk.rfa", 12, timestamp);
        IndexedFileState state = new IndexedFileState(file.FilePath, 12, timestamp, "hash");
        ThumbnailResult thumbnail = ThumbnailResult.Created("/thumbs/desk.png");
        FamilyParameter parameter = new FamilyParameter("Width", "6", "Double", true);
        FamilyMetadata metadata = new FamilyMetadata(
            file.FilePath, "Desk", "Furniture", "2024", new[] { "Standard" },
            new[] { parameter }, new[] { "approved" }, "Approved", "Interiors");
        FamilySearchQuery query = new FamilySearchQuery("Desk", "Furniture", "Approved", "Interiors", 25);
        FamilySearchResult result = new FamilySearchResult(
            1, metadata.DisplayName, metadata.SourcePath, metadata.Category,
            metadata.Status, metadata.Discipline, thumbnail.FilePath);

        Assert.AreSame(root, config.LibraryRoots[0]);
        Assert.AreEqual("hash", state.FileHash);
        Assert.AreEqual("Width", metadata.Parameters[0].Name);
        Assert.AreEqual("Double", parameter.StorageType);
        Assert.AreEqual(25, query.Limit);
        Assert.AreEqual("Desk", result.FamilyName);
        Assert.AreEqual("/thumbs/desk.png", result.ThumbnailPath);
    }

    [TestMethod]
    public void BoundaryModels_RejectInvalidValues()
    {
        Assert.ThrowsExactly<ArgumentOutOfRangeException>(
            () => new LibraryFileCandidate("/library/Desk.rfa", -1, DateTimeOffset.UtcNow));
        Assert.ThrowsExactly<ArgumentException>(() => ThumbnailResult.Created(" "));
        Assert.ThrowsExactly<ArgumentNullException>(
            () => new FileChangeDetector().Decide(null!, null));
    }

    [TestMethod]
    public void CollectionModels_DefensivelyCopyCallerOwnedValues()
    {
        LibraryRoot[] roots = { new LibraryRoot("/library", true, null, "Draft") };
        string[] types = { "Standard" };
        FamilyParameter[] parameters = { new FamilyParameter("Width", "6", "Double", true) };
        string[] tags = { "approved" };
        LibraryConfiguration configuration = new LibraryConfiguration(roots, "/db", "/thumbs");
        FamilyMetadata metadata = new FamilyMetadata(
            "/library/Desk.rfa", "Desk", "Furniture", "2024", types, parameters, tags, "Draft", null);

        roots[0] = new LibraryRoot("/other", true, null, "Draft");
        types[0] = "Mutated";
        parameters[0] = new FamilyParameter("Mutated", null, null, false);
        tags[0] = "mutated";

        Assert.AreEqual("/library", configuration.LibraryRoots[0].Path);
        Assert.AreEqual("Standard", metadata.TypeNames[0]);
        Assert.AreEqual("Width", metadata.Parameters[0].Name);
        Assert.AreEqual("approved", metadata.Tags[0]);
    }

    [TestMethod]
    public void ConfigurationProvider_RejectsMissingFile()
    {
        string missing = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"), "missing.json");
        Assert.ThrowsExactly<ConfigurationException>(
            () => new JsonLibraryConfigurationProvider().Load(missing));
    }
}
