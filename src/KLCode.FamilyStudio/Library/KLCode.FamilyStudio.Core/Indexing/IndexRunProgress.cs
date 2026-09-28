using System;

namespace KLCode.FamilyStudio.Core.Indexing;

public sealed class IndexRunProgress
{
    public IndexRunProgress(
        int totalFiles,
        int filesProcessed,
        int filesUpdated,
        int filesSkipped,
        int filesFailed,
        string? currentFilePath,
        bool isComplete)
    {
        if (totalFiles < 0) throw new ArgumentOutOfRangeException(nameof(totalFiles));
        if (filesProcessed < 0 || filesProcessed > totalFiles) throw new ArgumentOutOfRangeException(nameof(filesProcessed));
        if (filesUpdated < 0) throw new ArgumentOutOfRangeException(nameof(filesUpdated));
        if (filesSkipped < 0) throw new ArgumentOutOfRangeException(nameof(filesSkipped));
        if (filesFailed < 0) throw new ArgumentOutOfRangeException(nameof(filesFailed));

        TotalFiles = totalFiles;
        FilesProcessed = filesProcessed;
        FilesUpdated = filesUpdated;
        FilesSkipped = filesSkipped;
        FilesFailed = filesFailed;
        CurrentFilePath = currentFilePath;
        IsComplete = isComplete;
    }

    public int TotalFiles { get; }
    public int FilesProcessed { get; }
    public int FilesUpdated { get; }
    public int FilesSkipped { get; }
    public int FilesFailed { get; }
    public string? CurrentFilePath { get; }
    public bool IsComplete { get; }
}
