using KLA.ModelStartupImporter.Core;
using KLA.ModelStartupImporter.UI.ViewModels;
using Xunit;

namespace KLA.ModelStartupImporter.UI.Tests;

public sealed class StartupImporterViewModelTests
{
    [Fact]
    public void SourcePicker_RequiresBothSourcesToValidate()
    {
        StartupSourcePickerViewModel model = new StartupSourcePickerViewModel
        {
            ChecklistPath = "checklist.xlsx",
            SettingsPath = "settings.json",
        };

        Assert.False(model.CanReview);
        model.IsChecklistValid = true;
        Assert.False(model.CanReview);
        model.AreSettingsValid = true;
        Assert.True(model.CanReview);
    }

    [Fact]
    public void Review_ProjectsActionableExistingAndUncheckedRowsAndSelectionActions()
    {
        CatalogItem actionable = Catalog("D-001", "Target Detail");
        CatalogItem existing = Catalog("D-002", "Existing Detail");
        StartupImportSettings settings = Settings(actionable, existing);
        StartupDocumentModel document = Document(
            Item("D-001", "New Detail", true),
            Item("D-002", "Existing Detail", true),
            Item("D-003", "Unchecked Detail", false));
        StartupImportReview review = new StartupImportReviewBuilder().Build(
            document,
            settings.Catalog,
            new[] { "D-002" });

        StartupImportReviewViewModel model = new StartupImportReviewViewModel(document, settings, review, TestText);

        Assert.Equal(new[] { "Matched", "Existing", "Unchecked" }, model.Rows.Select(row => row.StatusTone));
        Assert.Equal(1, model.SelectedCount);
        Assert.True(model.CanImport);

        model.SelectNone();
        Assert.Equal(0, model.SelectedCount);
        Assert.False(model.CanImport);

        model.SelectAll();
        Assert.Equal(new[] { "D-001" }, model.GetSelectedItemIds());
    }

    [Fact]
    public void BlockingIssues_ReportUnknownAndDuplicateIdsAndKeepImportBlocked()
    {
        StartupImportSettings settings = Settings(Catalog("D-001", "Target Detail"));
        StartupDocumentModel document = Document(
            Item("D-001", "Duplicate A", true, "row 2"),
            Item("D-001", "Duplicate B", true, "row 3"),
            Item("X-999", "Unknown", true, "row 4"));
        StartupImportReview review = new StartupImportReviewBuilder().Build(document, settings.Catalog, Array.Empty<string>());

        StartupImportReviewViewModel reviewModel = new StartupImportReviewViewModel(document, settings, review, TestText);
        BlockingIssuesViewModel blockingModel = new BlockingIssuesViewModel(settings, review, TestText);

        Assert.True(review.Plan.HasBlockingIssues);
        Assert.False(reviewModel.CanImport);
        Assert.Single(blockingModel.UnknownItems);
        Assert.Single(blockingModel.DuplicateItems);
        Assert.Contains("X-999", blockingModel.BuildReport());
        Assert.Contains("D-001", blockingModel.BuildReport());
    }

    private static StartupImportSettings Settings(params CatalogItem[] items)
    {
        return new StartupImportSettings("seed.rvt", "2026.08", new ContentCatalog(items));
    }

    private static CatalogItem Catalog(string id, string target)
    {
        return new CatalogItem(id, id + " Source", target, StartupItemCategory.Detail, new[] { "3/32 in Arial" }, new[] { "Thin Lines" });
    }

    private static StartupDocumentModel Document(params StartupItem[] items)
    {
        return new StartupDocumentModel(
            "checklist.xlsx",
            StartupSourceType.Excel,
            DateTime.SpecifyKind(new DateTime(2026, 8, 31), DateTimeKind.Utc),
            new string('A', 64),
            items);
    }

    private static StartupItem Item(string id, string title, bool selected, string source = "row 2")
    {
        return new StartupItem(id, title, StartupItemCategory.Detail, selected, string.Empty, source, string.Empty);
    }

    private static string TestText(string key)
    {
        return key switch
        {
            "MatchedSummaryFormat" => "{0} matched",
            "ExistingSummaryFormat" => "{0} existing",
            "UncheckedSummaryFormat" => "{0} unchecked",
            "CatalogHashSummaryFormat" => "Catalog {0} / {1}",
            "WillCreateFormat" => "Will create {0}",
            "ImportOneItemFormat" => "Import {0} item",
            "ImportItemsFormat" => "Import {0} items",
            "UnknownOneHeadingFormat" => "{0} unknown in {1}",
            "UnknownHeadingFormat" => "{0} unknown in {1}",
            "DuplicateOneHeadingFormat" => "{0} duplicate",
            "DuplicateHeadingFormat" => "{0} duplicates",
            "ImportableHeadingFormat" => "{0} importable",
            _ => key,
        };
    }
}
