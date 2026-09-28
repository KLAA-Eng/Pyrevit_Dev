using System;
using KLCode.FamilyStudio.Core.Indexing;

namespace KLCode.FamilyStudio.Revit.Services;

/// <summary>
/// The explicit Revit refresh is intentionally a full metadata and preview
/// pass. Filesystem-only indexing remains incremental and lightweight.
/// </summary>
internal sealed class RevitFullRefreshChangeDetector : IChangeDetector
{
    public IndexDecision Decide(
        LibraryFileCandidate candidate,
        IndexedFileState? existing,
        string? currentHash = null)
    {
        if (candidate is null)
        {
            throw new ArgumentNullException(nameof(candidate));
        }

        return existing is null ? IndexDecision.New : IndexDecision.Changed;
    }
}
