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

    public StartupImportSelection CreateSelection(IEnumerable<string> selectedItemIds)
    {
        return StartupImportSelection.Create(this, selectedItemIds);
    }
}

/// <summary>
/// UI-owned selection intent. It contains only stable catalog item identifiers;
/// the Revit host rebuilds the review immediately before mutating a project.
/// </summary>
public sealed class StartupImportSelection
{
    private StartupImportSelection(IReadOnlyList<string> itemIds)
    {
        ItemIds = itemIds;
    }

    public IReadOnlyList<string> ItemIds { get; }

    public static StartupImportSelection Create(
        StartupImportReview review,
        IEnumerable<string> selectedItemIds)
    {
        if (review is null)
        {
            throw new ArgumentNullException(nameof(review));
        }

        if (selectedItemIds is null)
        {
            throw new ArgumentNullException(nameof(selectedItemIds));
        }

        HashSet<string> actionable = new HashSet<string>(
            review.ActionableMatches.Select(match => match.Item.ItemId),
            StringComparer.OrdinalIgnoreCase);
        List<string> selected = selectedItemIds
            .Where(itemId => !string.IsNullOrWhiteSpace(itemId))
            .Select(itemId => itemId.Trim())
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();
        if (selected.Count == 0)
        {
            throw new InvalidOperationException("Select at least one actionable startup item.");
        }

        if (selected.Any(itemId => !actionable.Contains(itemId)))
        {
            throw new InvalidOperationException(
                "The import selection contains an item that is not actionable in the current review.");
        }

        return new StartupImportSelection(new ReadOnlyCollection<string>(selected));
    }

    public IReadOnlyList<ImportMatch> Resolve(StartupImportReview review)
    {
        if (review is null)
        {
            throw new ArgumentNullException(nameof(review));
        }

        if (review.Plan.HasBlockingIssues)
        {
            throw new InvalidOperationException("Resolve unknown and duplicate selected checklist items before importing.");
        }

        HashSet<string> selected = new HashSet<string>(ItemIds, StringComparer.OrdinalIgnoreCase);
        ImportMatch[] matches = review.ActionableMatches
            .Where(match => selected.Contains(match.Item.ItemId))
            .ToArray();
        if (matches.Length != ItemIds.Count)
        {
            throw new InvalidOperationException(
                "The project changed after review; selected startup items must be reviewed again.");
        }

        return new ReadOnlyCollection<ImportMatch>(matches);
    }
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
