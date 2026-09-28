using System;
using System.Collections.Generic;
using System.Linq;
using KLA.ModelStartupImporter.Core;

namespace KLA.ModelStartupImporter.UI.ViewModels;

public sealed class BlockingIssuesViewModel
{
    public BlockingIssuesViewModel(
        StartupImportSettings settings,
        StartupImportReview review,
        Func<string, string>? text = null)
    {
        if (settings is null) throw new ArgumentNullException(nameof(settings));
        if (review is null) throw new ArgumentNullException(nameof(review));
        Func<string, string> getText = text ?? StartupImporterText.Get;

        UnknownItems = review.Plan.UnknownItems
            .Select(item => item.ItemId + " · " + item.Title)
            .ToArray();
        DuplicateItems = review.Plan.DuplicateItems
            .GroupBy(item => item.ItemId, StringComparer.OrdinalIgnoreCase)
            .Select(group => group.Key + " · selected " + group.Count() + "× · " +
                string.Join(", ", group.Select(item => item.SourceLocation)) + " · all excluded")
            .ToArray();
        UnknownHeading = string.Format(getText(UnknownItems.Count == 1 ? "UnknownOneHeadingFormat" : "UnknownHeadingFormat"), UnknownItems.Count, settings.CatalogVersion);
        DuplicateHeading = string.Format(getText(DuplicateItems.Count == 1 ? "DuplicateOneHeadingFormat" : "DuplicateHeadingFormat"), DuplicateItems.Count);
        ImportableHeading = string.Format(getText("ImportableHeadingFormat"), review.ActionableMatches.Count);
    }

    public IReadOnlyList<string> UnknownItems { get; }
    public IReadOnlyList<string> DuplicateItems { get; }
    public string UnknownHeading { get; }
    public string DuplicateHeading { get; }
    public string ImportableHeading { get; }

    public string BuildReport()
    {
        return string.Join("\n", new[]
        {
            UnknownHeading,
            string.Join("\n", UnknownItems),
            string.Empty,
            DuplicateHeading,
            string.Join("\n", DuplicateItems),
        });
    }
}
