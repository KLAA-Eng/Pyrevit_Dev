using System;
using System.IO;
using System.Text;

namespace KLCode.FamilyStudio.Core.Indexing;

public sealed class IndexRunStatusFileReporter : IProgress<IndexRunProgress>
{
    private readonly string _statusPath;
    private readonly Func<DateTimeOffset> _utcNow;

    public IndexRunStatusFileReporter(string statusPath, Func<DateTimeOffset>? utcNow = null)
    {
        if (string.IsNullOrWhiteSpace(statusPath)) throw new ArgumentException("A status path is required.", nameof(statusPath));

        _statusPath = Path.GetFullPath(statusPath);
        _utcNow = utcNow ?? (() => DateTimeOffset.UtcNow);
    }

    public void Report(IndexRunProgress value)
    {
        if (value is null) throw new ArgumentNullException(nameof(value));

        Write(
            value.IsComplete ? "complete" : "running",
            value.TotalFiles,
            value.FilesProcessed,
            value.FilesUpdated,
            value.FilesSkipped,
            value.FilesFailed,
            value.CurrentFilePath,
            null);
    }

    public void MarkStarting()
    {
        Write("starting", 0, 0, 0, 0, 0, null, null);
    }

    public void MarkFailed(string message)
    {
        Write("failed", 0, 0, 0, 0, 0, null, message);
    }

    private void Write(
        string state,
        int totalFiles,
        int filesProcessed,
        int filesUpdated,
        int filesSkipped,
        int filesFailed,
        string? currentFilePath,
        string? message)
    {
        string? temporaryPath = null;
        try
        {
            string? directory = Path.GetDirectoryName(_statusPath);
            if (!string.IsNullOrWhiteSpace(directory)) Directory.CreateDirectory(directory);

            temporaryPath = _statusPath + "." + Guid.NewGuid().ToString("N") + ".tmp";
            File.WriteAllText(temporaryPath, Format(
                state,
                totalFiles,
                filesProcessed,
                filesUpdated,
                filesSkipped,
                filesFailed,
                currentFilePath,
                message), new UTF8Encoding(false));
            File.Copy(temporaryPath, _statusPath, true);
        }
        catch (IOException)
        {
            // Refresh must continue when another process temporarily holds the status file.
        }
        catch (UnauthorizedAccessException)
        {
            // Status output is diagnostic only and must not prevent indexing.
        }
        finally
        {
            if (!string.IsNullOrWhiteSpace(temporaryPath) && File.Exists(temporaryPath))
            {
                try { File.Delete(temporaryPath); }
                catch (IOException) { }
                catch (UnauthorizedAccessException) { }
            }
        }
    }

    private string Format(
        string state,
        int totalFiles,
        int filesProcessed,
        int filesUpdated,
        int filesSkipped,
        int filesFailed,
        string? currentFilePath,
        string? message)
    {
        return string.Join("\n", new[]
        {
            "state=" + state,
            "updatedUtc=" + _utcNow().ToUniversalTime().ToString("O"),
            "totalFiles=" + totalFiles,
            "filesProcessed=" + filesProcessed,
            "filesUpdated=" + filesUpdated,
            "filesSkipped=" + filesSkipped,
            "filesFailed=" + filesFailed,
            "currentFilePath=" + Normalize(currentFilePath),
            "message=" + Normalize(message),
        }) + "\n";
    }

    private static string Normalize(string? value)
    {
        return (value ?? string.Empty).Replace("\r", " ").Replace("\n", " ");
    }
}
