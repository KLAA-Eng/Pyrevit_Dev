using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using KLCode.FamilyStudio.Core.Configuration;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;
using KLCode.FamilyStudio.Core.Repositories;
using KLCode.FamilyStudio.Core.Search;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace KLCode.FamilyStudio.Core.Tests;

[TestClass]
public sealed class LibraryIndexerTests
{
    [TestMethod]
    public async Task RunAsync_ContinuesAfterPerFileFailureAndSummarizesWork()
    {
        DateTimeOffset timestamp = new DateTimeOffset(2026, 8, 26, 12, 0, 0, TimeSpan.Zero);
        LibraryFileCandidate changed = new LibraryFileCandidate("/library/changed.rfa", 10, timestamp);
        LibraryFileCandidate unchanged = new LibraryFileCandidate("/library/unchanged.rfa", 20, timestamp);
        LibraryFileCandidate failing = new LibraryFileCandidate("/library/failing.rfa", 30, timestamp);
        FakeRepository repository = new FakeRepository();
        repository.Existing[unchanged.FilePath] = new IndexedFileState(unchanged.FilePath, 20, timestamp, null);
        FakeMetadataExtractor extractor = new FakeMetadataExtractor(failing.FilePath);
        LibraryIndexer indexer = new LibraryIndexer(
            new FakeScanner(new[] { changed, unchanged, failing }, Array.Empty<LibraryScanIssue>()),
            new FileChangeDetector(),
            extractor,
            new NoThumbnailService(),
            repository,
            () => timestamp);

        IndexRunSummary summary = await indexer.RunAsync(TestConfiguration(), CancellationToken.None);

        Assert.AreEqual(3, summary.FilesSeen);
        Assert.AreEqual(1, summary.FilesUpdated);
        Assert.AreEqual(1, summary.FilesSkipped);
        Assert.AreEqual(1, summary.FilesFailed);
        Assert.AreEqual(failing.FilePath, summary.Errors[0].FilePath);
        CollectionAssert.AreEquivalent(
            new[] { changed.FilePath, unchanged.FilePath, failing.FilePath },
            new List<string>(repository.MarkedSeen));
    }

    [TestMethod]
    public async Task RunAsync_DoesNotMarkMissingWhenAnyRootScanFails()
    {
        DateTimeOffset timestamp = new DateTimeOffset(2026, 8, 26, 12, 0, 0, TimeSpan.Zero);
        FakeRepository repository = new FakeRepository();
        LibraryIndexer indexer = new LibraryIndexer(
            new FakeScanner(Array.Empty<LibraryFileCandidate>(), new[] { new LibraryScanIssue("/missing", "missing") }),
            new FileChangeDetector(),
            new FakeMetadataExtractor(null),
            new NoThumbnailService(),
            repository,
            () => timestamp);

        IndexRunSummary summary = await indexer.RunAsync(TestConfiguration(), CancellationToken.None);

        Assert.AreEqual(1, summary.ScanIssues.Count);
        Assert.IsFalse(repository.WasMarkMissingCalled);
    }

    [TestMethod]
    public async Task RunAsync_RetainsPriorPreviewWhenPreviewRefreshFails()
    {
        DateTimeOffset timestamp = new DateTimeOffset(2026, 8, 30, 12, 0, 0, TimeSpan.Zero);
        LibraryFileCandidate changed = new LibraryFileCandidate("/library/changed.rfa", 11, timestamp);
        FakeRepository repository = new FakeRepository();
        repository.Existing[changed.FilePath] = new IndexedFileState(
            changed.FilePath,
            10,
            timestamp.AddMinutes(-1),
            null,
            "/thumbs/known-good.png");
        LibraryIndexer indexer = new LibraryIndexer(
            new FakeScanner(new[] { changed }, Array.Empty<LibraryScanIssue>()),
            new FileChangeDetector(),
            new FakeMetadataExtractor(null),
            new ThrowingThumbnailService(),
            repository,
            () => timestamp);

        IndexRunSummary summary = await indexer.RunAsync(TestConfiguration(), CancellationToken.None);

        Assert.AreEqual(1, summary.FilesUpdated);
        Assert.AreEqual(1, summary.FilesFailed);
        Assert.AreEqual("/thumbs/known-good.png", repository.Existing[changed.FilePath].ThumbnailPath);
        StringAssert.Contains(summary.Errors[0].Message, "prior preview was retained");
    }

    [TestMethod]
    public async Task RunAsync_IndexesFamilyWithoutPreviewWhenNewPreviewFails()
    {
        DateTimeOffset timestamp = new DateTimeOffset(2026, 8, 30, 12, 0, 0, TimeSpan.Zero);
        LibraryFileCandidate changed = new LibraryFileCandidate("/library/new.rfa", 11, timestamp);
        FakeRepository repository = new FakeRepository();
        LibraryIndexer indexer = new LibraryIndexer(
            new FakeScanner(new[] { changed }, Array.Empty<LibraryScanIssue>()),
            new FileChangeDetector(),
            new FakeMetadataExtractor(null),
            new ThrowingThumbnailService(),
            repository,
            () => timestamp);

        IndexRunSummary summary = await indexer.RunAsync(TestConfiguration(), CancellationToken.None);

        Assert.AreEqual(1, summary.FilesUpdated);
        Assert.AreEqual(1, summary.FilesFailed);
        Assert.IsTrue(repository.Existing.ContainsKey(changed.FilePath));
        Assert.IsNull(repository.Existing[changed.FilePath].ThumbnailPath);
        StringAssert.Contains(summary.Errors[0].Message, "indexed without a preview");
    }

    private static LibraryConfiguration TestConfiguration()
    {
        return new LibraryConfiguration(
            new[] { new LibraryRoot("/library", true, null, "Draft") },
            Path.Combine(Path.GetTempPath(), "family-studio-indexer.sqlite"),
            Path.Combine(Path.GetTempPath(), "family-studio-thumbnails"));
    }

    private sealed class FakeScanner : ILibraryScanner
    {
        private readonly LibraryScanResult _result;

        public FakeScanner(IReadOnlyList<LibraryFileCandidate> files, IReadOnlyList<LibraryScanIssue> issues)
        {
            _result = new LibraryScanResult(files, issues);
        }

        public LibraryScanResult Scan(LibraryConfiguration configuration)
        {
            return _result;
        }
    }

    private sealed class FakeMetadataExtractor : IMetadataExtractor
    {
        private readonly string? _failingPath;

        public FakeMetadataExtractor(string? failingPath)
        {
            _failingPath = failingPath;
        }

        public Task<FamilyMetadata> ExtractAsync(string filePath, CancellationToken cancellationToken)
        {
            if (string.Equals(filePath, _failingPath, StringComparison.Ordinal))
            {
                throw new InvalidDataException("invalid family fixture");
            }

            return Task.FromResult(new FamilyMetadata(
                filePath,
                Path.GetFileNameWithoutExtension(filePath),
                null,
                null,
                Array.Empty<string>(),
                Array.Empty<FamilyParameter>(),
                Array.Empty<string>(),
                "Draft",
                null));
        }
    }

    private sealed class NoThumbnailService : IThumbnailService
    {
        public Task<ThumbnailResult> EnsureThumbnailAsync(
            FamilyMetadata metadata,
            string thumbnailDirectory,
            CancellationToken cancellationToken)
        {
            return Task.FromResult(ThumbnailResult.None);
        }
    }

    private sealed class ThrowingThumbnailService : IThumbnailService
    {
        public Task<ThumbnailResult> EnsureThumbnailAsync(
            FamilyMetadata metadata,
            string thumbnailDirectory,
            CancellationToken cancellationToken)
        {
            throw new InvalidOperationException("preview fixture failure");
        }
    }

    private sealed class FakeRepository : IFamilyRepository
    {
        public Dictionary<string, IndexedFileState> Existing { get; } = new Dictionary<string, IndexedFileState>();
        public IReadOnlyCollection<string> MarkedSeen { get; private set; } = Array.Empty<string>();
        public bool WasMarkMissingCalled { get; private set; }

        public IndexedFileState? GetIndexedFile(string filePath)
        {
            return Existing.TryGetValue(filePath, out IndexedFileState? state) ? state : null;
        }

        public void Upsert(
            FamilyMetadata metadata,
            LibraryFileCandidate file,
            ThumbnailResult thumbnail,
            DateTimeOffset indexedUtc)
        {
            Existing[file.FilePath] = new IndexedFileState(file.FilePath, file.FileSize, file.ModifiedUtc, null, thumbnail.FilePath);
        }

        public IReadOnlyList<FamilySearchResult> Search(FamilySearchQuery query)
        {
            return Array.Empty<FamilySearchResult>();
        }

        public FamilyDetail? GetDetail(long familyId)
        {
            return null;
        }

        public void SetFavorite(long familyId, bool isFavorite)
        {
        }

        public IReadOnlyList<FamilySearchResult> GetFavorites(int limit)
        {
            return Array.Empty<FamilySearchResult>();
        }

        public void RecordUse(long familyId, FamilyUseAction action, DateTimeOffset usedUtc)
        {
        }

        public IReadOnlyList<FamilySearchResult> GetRecent(int limit)
        {
            return Array.Empty<FamilySearchResult>();
        }

        public void MarkMissingFiles(
            IReadOnlyCollection<string> seenPaths,
            IReadOnlyCollection<string> scannedRootPaths)
        {
            WasMarkMissingCalled = true;
            MarkedSeen = seenPaths;
        }
    }
}
