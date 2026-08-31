using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;

namespace KLA.ModelStartupImporter.Core;

public interface IStartupSettingsProvider
{
    StartupImportSettings Load(string settingsPath);
}

public sealed class StartupImportSettings
{
    public StartupImportSettings(string seedModelPath, string catalogVersion, ContentCatalog catalog)
    {
        if (string.IsNullOrWhiteSpace(seedModelPath))
        {
            throw new ArgumentException("A seed model path is required.", nameof(seedModelPath));
        }

        if (string.IsNullOrWhiteSpace(catalogVersion))
        {
            throw new ArgumentException("A catalog version is required.", nameof(catalogVersion));
        }

        SeedModelPath = Path.GetFullPath(seedModelPath);
        CatalogVersion = catalogVersion.Trim();
        Catalog = catalog ?? throw new ArgumentNullException(nameof(catalog));
    }

    public string SeedModelPath { get; }
    public string CatalogVersion { get; }
    public ContentCatalog Catalog { get; }
}

public sealed class StartupImportReview
{
    public StartupImportReview(ImportPlan plan, IReadOnlyList<ImportMatch> existingMatches)
    {
        Plan = plan ?? throw new ArgumentNullException(nameof(plan));
        if (existingMatches is null)
        {
            throw new ArgumentNullException(nameof(existingMatches));
        }

        ImportMatch[] existing = existingMatches.ToArray();
        if (existing.Any(match => match is null))
        {
            throw new ArgumentException("Existing matches cannot contain null values.", nameof(existingMatches));
        }

        ExistingMatches = new ReadOnlyCollection<ImportMatch>(existing);
        HashSet<string> existingIds = new HashSet<string>(
            existing.Select(match => match.Item.ItemId), StringComparer.OrdinalIgnoreCase);
        ActionableMatches = new ReadOnlyCollection<ImportMatch>(
            plan.Matches.Where(match => !existingIds.Contains(match.Item.ItemId)).ToArray());
    }

    public ImportPlan Plan { get; }
    public IReadOnlyList<ImportMatch> ExistingMatches { get; }
    public IReadOnlyList<ImportMatch> ActionableMatches { get; }
    public bool CanImport => !Plan.HasBlockingIssues && ActionableMatches.Count > 0;
}

public sealed class StartupImportReviewBuilder
{
    public StartupImportReview Build(
        StartupDocumentModel document,
        ContentCatalog catalog,
        IEnumerable<string> existingItemIds)
    {
        if (existingItemIds is null)
        {
            throw new ArgumentNullException(nameof(existingItemIds));
        }

        ImportPlan plan = new ImportPlanBuilder().Build(document, catalog);
        HashSet<string> existing = new HashSet<string>(
            existingItemIds.Where(id => !string.IsNullOrWhiteSpace(id)).Select(id => id.Trim()),
            StringComparer.OrdinalIgnoreCase);
        return new StartupImportReview(
            plan,
            plan.Matches.Where(match => existing.Contains(match.Item.ItemId)).ToArray());
    }
}
