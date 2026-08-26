using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;

namespace KLCode.FamilyStudio.Indexer;

internal sealed class FileSystemMetadataExtractor : IMetadataExtractor
{
    public Task<FamilyMetadata> ExtractAsync(string filePath, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (string.IsNullOrWhiteSpace(filePath) || !File.Exists(filePath))
        {
            throw new FileNotFoundException("The scanned family file is no longer available.", filePath);
        }

        FamilyMetadata metadata = new FamilyMetadata(
            filePath,
            Path.GetFileNameWithoutExtension(filePath),
            null,
            null,
            Array.Empty<string>(),
            Array.Empty<FamilyParameter>(),
            Array.Empty<string>(),
            "Draft",
            null);
        return Task.FromResult(metadata);
    }
}

internal sealed class NoThumbnailService : IThumbnailService
{
    public Task<ThumbnailResult> EnsureThumbnailAsync(
        FamilyMetadata metadata,
        string thumbnailDirectory,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(ThumbnailResult.None);
    }
}
