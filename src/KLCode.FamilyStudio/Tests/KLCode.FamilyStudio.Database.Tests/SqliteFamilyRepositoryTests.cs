using System;
using System.Collections.Generic;
using System.IO;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;
using KLCode.FamilyStudio.Core.Search;
using KLCode.FamilyStudio.Database.Repositories;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace KLCode.FamilyStudio.Database.Tests;

[TestClass]
public sealed class SqliteFamilyRepositoryTests
{
    private string _directory = null!;
    private SqliteFamilyRepository _repository = null!;

    [TestInitialize]
    public void SetUp()
    {
        _directory = Path.Combine(Path.GetTempPath(), "family-studio-db-tests", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_directory);
        _repository = new SqliteFamilyRepository(Path.Combine(_directory, "families.sqlite"));
    }

    [TestCleanup]
    public void TearDown()
    {
        _repository.Dispose();
        Directory.Delete(_directory, true);
    }

    [TestMethod]
    public void UpsertAndSearch_FindsFamilyByTypeTagAndParameter()
    {
        DateTimeOffset timestamp = new DateTimeOffset(2026, 8, 26, 12, 0, 0, TimeSpan.Zero);
        FamilyMetadata metadata = new FamilyMetadata(
            "/library/Conference Table.rfa",
            "Conference Table",
            "Furniture",
            "2024",
            new[] { "Six Person", "Eight Person" },
            new[] { new FamilyParameter("Manufacturer", "KL&A", "String", true) },
            new[] { "approved", "conference" },
            "Approved",
            "Interiors");
        LibraryFileCandidate file = new LibraryFileCandidate(metadata.SourcePath, 4200, timestamp);

        _repository.Upsert(metadata, file, ThumbnailResult.None, timestamp);

        Assert.AreEqual(1, _repository.Search(new FamilySearchQuery("Eight Person", null, null, null, 25)).Count);
        Assert.AreEqual(1, _repository.Search(new FamilySearchQuery("approved", null, null, null, 25)).Count);
        Assert.AreEqual(1, _repository.Search(new FamilySearchQuery("KL&A", null, null, null, 25)).Count);
        Assert.AreEqual(0, _repository.Search(new FamilySearchQuery("door", null, null, null, 25)).Count);
    }

    [TestMethod]
    public void Search_ValidatesLimitBoundary()
    {
        Assert.ThrowsExactly<ArgumentOutOfRangeException>(
            () => _repository.Search(new FamilySearchQuery(null, null, null, null, 0)));
        Assert.ThrowsExactly<ArgumentOutOfRangeException>(
            () => _repository.Search(new FamilySearchQuery(null, null, null, null, 201)));
    }

    [TestMethod]
    public void Upsert_DeduplicatesRepeatedTypeAndTagValues()
    {
        DateTimeOffset timestamp = new DateTimeOffset(2026, 8, 26, 12, 0, 0, TimeSpan.Zero);
        FamilyMetadata metadata = new FamilyMetadata(
            "/library/Chair.rfa",
            "Chair",
            "Furniture",
            "2024",
            new[] { "Standard", "Standard" },
            Array.Empty<FamilyParameter>(),
            new[] { "approved", "approved" },
            "Approved",
            "Interiors");

        _repository.Upsert(
            metadata,
            new LibraryFileCandidate(metadata.SourcePath, 100, timestamp),
            ThumbnailResult.None,
            timestamp);

        Assert.AreEqual(1, _repository.Search(new FamilySearchQuery("Standard", null, null, null, 25)).Count);
        Assert.AreEqual(1, _repository.Search(new FamilySearchQuery("approved", null, null, null, 25)).Count);
    }

    [TestMethod]
    public void MarkMissing_SoftDeletesOnlyUnseenRecords()
    {
        DateTimeOffset timestamp = new DateTimeOffset(2026, 8, 26, 12, 0, 0, TimeSpan.Zero);
        UpsertMinimal("/library/keep.rfa", timestamp);
        UpsertMinimal("/library/missing.rfa", timestamp);

        _repository.MarkMissingFiles(
            new[] { "/library/keep.rfa" },
            new[] { "/library" });

        Assert.AreEqual(1, _repository.Search(new FamilySearchQuery(null, null, null, null, 25)).Count);
        Assert.IsNull(_repository.GetIndexedFile("/library/missing.rfa"));
    }

    [TestMethod]
    public void MarkMissing_OnlyChangesFamiliesUnderSuccessfullyScannedRoots()
    {
        DateTimeOffset timestamp = new DateTimeOffset(2026, 8, 26, 12, 0, 0, TimeSpan.Zero);
        UpsertMinimal("/library/a/keep.rfa", timestamp);
        UpsertMinimal("/library/a/missing.rfa", timestamp);
        UpsertMinimal("/library/b/unrelated.rfa", timestamp);

        _repository.MarkMissingFiles(
            new[] { "/library/a/keep.rfa" },
            new[] { "/library/a" });

        Assert.IsNotNull(_repository.GetIndexedFile("/library/a/keep.rfa"));
        Assert.IsNull(_repository.GetIndexedFile("/library/a/missing.rfa"));
        Assert.IsNotNull(_repository.GetIndexedFile("/library/b/unrelated.rfa"));
    }

    private void UpsertMinimal(string path, DateTimeOffset timestamp)
    {
        FamilyMetadata metadata = new FamilyMetadata(
            path,
            Path.GetFileNameWithoutExtension(path),
            null,
            null,
            Array.Empty<string>(),
            Array.Empty<FamilyParameter>(),
            Array.Empty<string>(),
            "Draft",
            null);
        _repository.Upsert(metadata, new LibraryFileCandidate(path, 10, timestamp), ThumbnailResult.None, timestamp);
    }
}
