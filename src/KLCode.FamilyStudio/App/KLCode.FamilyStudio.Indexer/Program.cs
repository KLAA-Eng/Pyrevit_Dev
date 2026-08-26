using System;
using System.Threading;
using System.Threading.Tasks;
using KLCode.FamilyStudio.Core.Configuration;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Database.Repositories;

namespace KLCode.FamilyStudio.Indexer;

internal static class Program
{
    public static async Task<int> Main(string[] args)
    {
        if (!TryGetConfigurationPath(args, out string? configurationPath))
        {
            Console.Error.WriteLine("Usage: KLCode.FamilyStudio.Indexer --config <configuration.json>");
            return 2;
        }

        try
        {
            return await RunAsync(configurationPath!, CancellationToken.None).ConfigureAwait(false);
        }
        catch (ConfigurationException exception)
        {
            Console.Error.WriteLine("Configuration error: " + exception.Message);
            return 2;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine("Indexing could not start: " + exception.Message);
            return 1;
        }
    }

    private static async Task<int> RunAsync(string configurationPath, CancellationToken cancellationToken)
    {
        LibraryConfiguration configuration = new JsonLibraryConfigurationProvider().Load(configurationPath);
        using SqliteFamilyRepository repository = new SqliteFamilyRepository(configuration.DatabasePath);
        LibraryIndexer indexer = new LibraryIndexer(
            new FileSystemLibraryScanner(),
            new FileChangeDetector(),
            new FileSystemMetadataExtractor(),
            new NoThumbnailService(),
            repository,
            () => DateTimeOffset.UtcNow);

        Console.WriteLine("Metadata mode: filesystem-only; Revit category, type, parameter, and thumbnail data are not extracted by this process.");
        IndexRunSummary summary = await indexer.RunAsync(configuration, cancellationToken).ConfigureAwait(false);
        WriteSummary(summary);
        return summary.FilesFailed == 0 && summary.ScanIssues.Count == 0 ? 0 : 1;
    }

    private static bool TryGetConfigurationPath(string[] args, out string? path)
    {
        path = null;
        if (args is null || args.Length != 2 || !string.Equals(args[0], "--config", StringComparison.Ordinal))
        {
            return false;
        }

        path = string.IsNullOrWhiteSpace(args[1]) ? null : args[1];
        return path is not null;
    }

    private static void WriteSummary(IndexRunSummary summary)
    {
        Console.WriteLine(
            "Seen: {0}; updated: {1}; skipped: {2}; failed: {3}; scan issues: {4}",
            summary.FilesSeen,
            summary.FilesUpdated,
            summary.FilesSkipped,
            summary.FilesFailed,
            summary.ScanIssues.Count);
        foreach (LibraryScanIssue issue in summary.ScanIssues)
        {
            Console.Error.WriteLine("Scan issue [{0}]: {1}", issue.Path, issue.Message);
        }

        foreach (IndexRunError error in summary.Errors)
        {
            Console.Error.WriteLine("File failed [{0}]: {1}", error.FilePath, error.Message);
        }
    }
}
