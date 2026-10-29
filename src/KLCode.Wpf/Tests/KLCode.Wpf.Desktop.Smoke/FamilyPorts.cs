using System;
using System.Collections.Generic;
using KLCode.FamilyStudio.Core.Configuration;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;
using KLCode.FamilyStudio.Core.Repositories;
using KLCode.FamilyStudio.Core.Search;
using KLCode.FamilyStudio.Revit.Services;

internal sealed class EmptyFamilyRepository : IFamilyRepository
{
    public IndexedFileState? GetIndexedFile(string path) => null;
    public IReadOnlyList<FamilySearchResult> Search(FamilySearchQuery query) => Array.Empty<FamilySearchResult>();
    public FamilyCatalogFilterOptions GetFilterOptions() => new FamilyCatalogFilterOptions(
        Array.Empty<string>(), Array.Empty<string>(), Array.Empty<string>(), Array.Empty<string>());
    public FamilyDetail? GetDetail(long id) => null;
    public IReadOnlyList<FamilySearchResult> GetFavorites(int limit) => Array.Empty<FamilySearchResult>();
    public IReadOnlyList<FamilySearchResult> GetRecent(int limit) => Array.Empty<FamilySearchResult>();
    public void Upsert(FamilyMetadata metadata, LibraryFileCandidate file, ThumbnailResult thumbnail, DateTimeOffset indexedUtc) => Forbidden();
    public void SyncLibraryRoots(IReadOnlyList<LibraryRoot> roots) => Forbidden();
    public void SetFavorite(long id, bool favorite) => Forbidden();
    public void RecordUse(long id, FamilyUseAction action, DateTimeOffset usedUtc) => Forbidden();
    public void MarkMissingFiles(IReadOnlyCollection<string> seenPaths, IReadOnlyCollection<string> roots) => Forbidden();
    private static void Forbidden() => throw new InvalidOperationException("The UI constructor must not mutate the repository.");
}

internal sealed class ForbiddenFamilyLoadService : IFamilyLoadService
{
    public void Load(FamilySearchResult family) => Forbidden();
    public void LoadAndPlace(FamilySearchResult family) => Forbidden();
    public void LoadBatch(IReadOnlyList<FamilySearchResult> families) => Forbidden();
    private static void Forbidden() => throw new InvalidOperationException("The desktop smoke check must never invoke model operations.");
}
