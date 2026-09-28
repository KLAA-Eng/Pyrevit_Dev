using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;
using KLCode.FamilyStudio.Core.Configuration;
using KLCode.FamilyStudio.Core.Models;
using KLCode.FamilyStudio.Core.Repositories;

namespace KLCode.FamilyStudio.Core.Indexing;

public sealed class IndexRunError
{
    public IndexRunError(string filePath, string message)
    {
        FilePath = filePath;
        Message = message;
    }

    public string FilePath { get; }
    public string Message { get; }
}

public sealed class IndexRunSummary
{
    public IndexRunSummary(
        int filesSeen,
        int filesUpdated,
        int filesSkipped,
        IReadOnlyList<IndexRunError> errors,
        IReadOnlyList<LibraryScanIssue> scanIssues)
    {
        FilesSeen = filesSeen;
        FilesUpdated = filesUpdated;
        FilesSkipped = filesSkipped;
        Errors = Copy(errors, nameof(errors));
        ScanIssues = Copy(scanIssues, nameof(scanIssues));
    }

    public int FilesSeen { get; }
    public int FilesUpdated { get; }
    public int FilesSkipped { get; }
    public int FilesFailed => Errors.Count;
    public IReadOnlyList<IndexRunError> Errors { get; }
    public IReadOnlyList<LibraryScanIssue> ScanIssues { get; }

    private static IReadOnlyList<T> Copy<T>(IReadOnlyList<T> values, string parameterName)
    {
        if (values is null)
        {
            throw new ArgumentNullException(parameterName);
        }

        T[] copy = values.ToArray();
        if (copy.Any(value => value is null))
        {
            throw new ArgumentException("Collection values cannot contain null entries.", parameterName);
        }

        return new ReadOnlyCollection<T>(copy);
    }
}

public sealed class LibraryIndexer
{
    private readonly ILibraryScanner _scanner;
    private readonly IChangeDetector _changeDetector;
    private readonly IMetadataExtractor _metadataExtractor;
    private readonly IThumbnailService _thumbnailService;
    private readonly IFamilyRepository _repository;
    private readonly Func<DateTimeOffset> _utcNow;

    public LibraryIndexer(
        ILibraryScanner scanner,
        IChangeDetector changeDetector,
        IMetadataExtractor metadataExtractor,
        IThumbnailService thumbnailService,
        IFamilyRepository repository,
        Func<DateTimeOffset> utcNow)
    {
        _scanner = scanner ?? throw new ArgumentNullException(nameof(scanner));
        _changeDetector = changeDetector ?? throw new ArgumentNullException(nameof(changeDetector));
        _metadataExtractor = metadataExtractor ?? throw new ArgumentNullException(nameof(metadataExtractor));
        _thumbnailService = thumbnailService ?? throw new ArgumentNullException(nameof(thumbnailService));
        _repository = repository ?? throw new ArgumentNullException(nameof(repository));
        _utcNow = utcNow ?? throw new ArgumentNullException(nameof(utcNow));
    }

    public async Task<IndexRunSummary> RunAsync(
        LibraryConfiguration configuration,
        CancellationToken cancellationToken,
        IProgress<IndexRunProgress>? progress = null)
    {
        if (configuration is null)
        {
            throw new ArgumentNullException(nameof(configuration));
        }

        LibraryScanResult scan = _scanner.Scan(configuration);
        ReportProgress(progress, scan.Files.Count, 0, 0, 0, 0, null, false);
        _repository.SyncLibraryRoots(configuration.LibraryRoots);
        List<IndexRunError> errors = new List<IndexRunError>();
        int updated = 0;
        int skipped = 0;
        int processed = 0;
        foreach (LibraryFileCandidate file in scan.Files)
        {
            cancellationToken.ThrowIfCancellationRequested();
            ReportProgress(progress, scan.Files.Count, processed, updated, skipped, errors.Count, file.FilePath, false);
            IndexedFileState? existing = _repository.GetIndexedFile(file.FilePath);
            IndexDecision decision = _changeDetector.Decide(file, existing);
            if (decision == IndexDecision.Unchanged)
            {
                skipped++;
                processed++;
                continue;
            }

            bool wasUpdated = await TryUpdateAsync(file, existing, configuration, errors, cancellationToken).ConfigureAwait(false);
            updated += wasUpdated ? 1 : 0;
            processed++;
        }

        if (scan.Issues.Count == 0)
        {
            _repository.MarkMissingFiles(
                scan.Files.Select(file => file.FilePath).ToArray(),
                configuration.LibraryRoots
                    .Where(root => root.IsEnabled)
                    .Select(root => root.Path)
                    .ToArray());
        }

        IndexRunSummary summary = new IndexRunSummary(scan.Files.Count, updated, skipped, errors.AsReadOnly(), scan.Issues);
        ReportProgress(progress, scan.Files.Count, processed, updated, skipped, errors.Count, null, true);
        return summary;
    }

    private async Task<bool> TryUpdateAsync(
        LibraryFileCandidate file,
        IndexedFileState? existing,
        LibraryConfiguration configuration,
        ICollection<IndexRunError> errors,
        CancellationToken cancellationToken)
    {
        try
        {
            LibraryFileCandidate indexedFile = new LibraryFileCandidate(
                file.FilePath,
                file.FileSize,
                file.ModifiedUtc,
                CreateSha256(file.FilePath));
            FamilyMetadata metadata = await _metadataExtractor
                .ExtractAsync(file.FilePath, cancellationToken)
                .ConfigureAwait(false);
            ThumbnailResult thumbnail;
            try
            {
                thumbnail = await _thumbnailService
                    .EnsureThumbnailAsync(metadata, configuration.ThumbnailDirectory, cancellationToken)
                    .ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                throw;
            }
            catch (Exception exception)
            {
                bool retainedPriorPreview = !string.IsNullOrWhiteSpace(existing?.ThumbnailPath);
                thumbnail = retainedPriorPreview
                    ? ThumbnailResult.Created(existing!.ThumbnailPath!)
                    : ThumbnailResult.None;
                errors.Add(new IndexRunError(
                    file.FilePath,
                    retainedPriorPreview
                        ? "Preview refresh failed; the prior preview was retained. " + exception.Message
                        : "Preview refresh failed; the family was indexed without a preview. " + exception.Message));
            }
            _repository.Upsert(metadata, indexedFile, thumbnail, _utcNow());
            return true;
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception exception)
        {
            errors.Add(new IndexRunError(file.FilePath, exception.Message));
            return false;
        }
    }

    private static string? CreateSha256(string filePath)
    {
        // Test doubles and failed network files can be represented by a scan
        // candidate without an accessible local stream. Metadata extraction
        // remains responsible for reporting those failures.
        if (!File.Exists(filePath))
        {
            return null;
        }

        using FileStream stream = File.OpenRead(filePath);
        using SHA256 hash = SHA256.Create();
        return BitConverter.ToString(hash.ComputeHash(stream)).Replace("-", string.Empty);
    }

    private static void ReportProgress(
        IProgress<IndexRunProgress>? progress,
        int totalFiles,
        int filesProcessed,
        int filesUpdated,
        int filesSkipped,
        int filesFailed,
        string? currentFilePath,
        bool isComplete)
    {
        progress?.Report(new IndexRunProgress(
            totalFiles,
            filesProcessed,
            filesUpdated,
            filesSkipped,
            filesFailed,
            currentFilePath,
            isComplete));
    }
}
