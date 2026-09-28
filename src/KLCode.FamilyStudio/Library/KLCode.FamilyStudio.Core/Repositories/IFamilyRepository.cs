using System;
using System.Collections.Generic;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;
using KLCode.FamilyStudio.Core.Configuration;
using KLCode.FamilyStudio.Core.Search;

namespace KLCode.FamilyStudio.Core.Repositories;

public interface IFamilyRepository
{
    IndexedFileState? GetIndexedFile(string filePath);
    void Upsert(FamilyMetadata metadata, LibraryFileCandidate file, ThumbnailResult thumbnail, DateTimeOffset indexedUtc);
    void SyncLibraryRoots(IReadOnlyList<LibraryRoot> roots);
    IReadOnlyList<FamilySearchResult> Search(FamilySearchQuery query);
    FamilyCatalogFilterOptions GetFilterOptions();
    FamilyDetail? GetDetail(long familyId);
    void SetFavorite(long familyId, bool isFavorite);
    IReadOnlyList<FamilySearchResult> GetFavorites(int limit);
    void RecordUse(long familyId, FamilyUseAction action, DateTimeOffset usedUtc);
    IReadOnlyList<FamilySearchResult> GetRecent(int limit);
    void MarkMissingFiles(
        IReadOnlyCollection<string> seenPaths,
        IReadOnlyCollection<string> scannedRootPaths);
}
