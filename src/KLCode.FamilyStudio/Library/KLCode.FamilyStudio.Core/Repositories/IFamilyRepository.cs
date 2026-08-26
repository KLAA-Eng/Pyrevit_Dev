using System;
using System.Collections.Generic;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;
using KLCode.FamilyStudio.Core.Search;

namespace KLCode.FamilyStudio.Core.Repositories;

public interface IFamilyRepository
{
    IndexedFileState? GetIndexedFile(string filePath);
    void Upsert(FamilyMetadata metadata, LibraryFileCandidate file, ThumbnailResult thumbnail, DateTimeOffset indexedUtc);
    IReadOnlyList<FamilySearchResult> Search(FamilySearchQuery query);
    void MarkMissingFiles(
        IReadOnlyCollection<string> seenPaths,
        IReadOnlyCollection<string> scannedRootPaths);
}
