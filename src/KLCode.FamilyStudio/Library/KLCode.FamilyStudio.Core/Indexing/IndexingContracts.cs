using System.Threading;
using System.Threading.Tasks;
using KLCode.FamilyStudio.Core.Configuration;
using KLCode.FamilyStudio.Core.Models;

namespace KLCode.FamilyStudio.Core.Indexing;

public interface ILibraryScanner
{
    LibraryScanResult Scan(LibraryConfiguration configuration);
}

public interface IChangeDetector
{
    IndexDecision Decide(
        LibraryFileCandidate candidate,
        IndexedFileState? existing,
        string? currentHash = null);
}

public interface IMetadataExtractor
{
    Task<FamilyMetadata> ExtractAsync(string filePath, CancellationToken cancellationToken);
}

public interface IThumbnailService
{
    Task<ThumbnailResult> EnsureThumbnailAsync(
        FamilyMetadata metadata,
        string thumbnailDirectory,
        CancellationToken cancellationToken);
}
