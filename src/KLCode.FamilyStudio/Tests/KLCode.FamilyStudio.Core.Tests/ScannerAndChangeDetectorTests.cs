using System;
using System.IO;
using KLCode.FamilyStudio.Core.Configuration;
using KLCode.FamilyStudio.Core.Indexing;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace KLCode.FamilyStudio.Core.Tests;

[TestClass]
public sealed class ScannerAndChangeDetectorTests
{
    [TestMethod]
    public void Scan_ReturnsOnlyRfaFilesInDeterministicOrder()
    {
        using TempDirectory temp = new TempDirectory();
        string root = temp.CreateDirectory("library");
        temp.WriteFile("library/zeta.RFA", "z");
        temp.WriteFile("library/readme.txt", "ignore");
        temp.WriteFile("library/nested/alpha.rfa", "a");
        LibraryConfiguration config = TestConfiguration(root, temp.Path);

        LibraryScanResult result = new FileSystemLibraryScanner().Scan(config);

        Assert.AreEqual(2, result.Files.Count);
        Assert.AreEqual("alpha.rfa", Path.GetFileName(result.Files[0].FilePath));
        Assert.AreEqual("zeta.RFA", Path.GetFileName(result.Files[1].FilePath));
        Assert.AreEqual(0, result.Issues.Count);
    }

    [TestMethod]
    public void Scan_ReportsMissingRootWithoutInventingFiles()
    {
        using TempDirectory temp = new TempDirectory();
        LibraryConfiguration config = TestConfiguration(Path.Combine(temp.Path, "missing"), temp.Path);

        LibraryScanResult result = new FileSystemLibraryScanner().Scan(config);

        Assert.AreEqual(0, result.Files.Count);
        Assert.AreEqual(1, result.Issues.Count);
    }

    [TestMethod]
    public void Scan_DeduplicatesFilesFromOverlappingRoots()
    {
        using TempDirectory temp = new TempDirectory();
        string root = temp.CreateDirectory("library");
        temp.WriteFile("library/Desk.rfa", "fixture");
        LibraryConfiguration config = new LibraryConfiguration(
            new[]
            {
                new LibraryRoot(root, true, null, "Draft"),
                new LibraryRoot(root, true, null, "Draft"),
            },
            Path.Combine(temp.Path, "index.sqlite"),
            Path.Combine(temp.Path, "thumbs"));

        LibraryScanResult result = new FileSystemLibraryScanner().Scan(config);

        Assert.AreEqual(1, result.Files.Count);
        Assert.AreEqual(0, result.Issues.Count);
    }

    [TestMethod]
    public void Decide_UsesSizeTimestampAndOptionalHash()
    {
        DateTimeOffset modified = new DateTimeOffset(2026, 8, 26, 12, 0, 0, TimeSpan.Zero);
        LibraryFileCandidate candidate = new LibraryFileCandidate("C:\\library\\Desk.rfa", 100, modified);
        FileChangeDetector detector = new FileChangeDetector();

        Assert.AreEqual(IndexDecision.New, detector.Decide(candidate, null));
        Assert.AreEqual(
            IndexDecision.Unchanged,
            detector.Decide(candidate, new IndexedFileState(candidate.FilePath, 100, modified, null)));
        Assert.AreEqual(
            IndexDecision.Changed,
            detector.Decide(candidate, new IndexedFileState(candidate.FilePath, 101, modified, null)));
        Assert.AreEqual(
            IndexDecision.Changed,
            detector.Decide(candidate, new IndexedFileState(candidate.FilePath, 100, modified, "different"), "actual"));
    }

    private static LibraryConfiguration TestConfiguration(string root, string basePath)
    {
        return new LibraryConfiguration(
            new[] { new LibraryRoot(root, true, null, "Draft") },
            Path.Combine(basePath, "index.sqlite"),
            Path.Combine(basePath, "thumbs"));
    }
}
