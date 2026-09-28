using System;

namespace KLCode.FamilyStudio.Core.Indexing;

public sealed class FileChangeDetector : IChangeDetector
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

        if (existing is null)
        {
            return IndexDecision.New;
        }

        bool hasSameStat = candidate.FileSize == existing.FileSize &&
            candidate.ModifiedUtc.Equals(existing.ModifiedUtc);
        bool hasHashMismatch = currentHash is not null &&
            existing.FileHash is not null &&
            !string.Equals(currentHash, existing.FileHash, StringComparison.Ordinal);
        return hasSameStat && !hasHashMismatch ? IndexDecision.Unchanged : IndexDecision.Changed;
    }
}
