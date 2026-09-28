using KLA.ModelStartupImporter.Core;

namespace KLA.ModelStartupImporter.Tests;

public sealed class ImportPlanBuilderTests
{
    [Fact]
    public void Build_ClassifiesMatchedUnknownSkippedAndDuplicateItems()
    {
        var document = TestModels.Document(
            TestModels.Item("D-001", selected: true),
            TestModels.Item("D-002", selected: true),
            TestModels.Item("D-003", selected: false),
            TestModels.Item("D-004", selected: true),
            TestModels.Item("d-004", selected: true));
        var catalog = new ContentCatalog(new[]
        {
            TestModels.CatalogItem("D-001"),
            TestModels.CatalogItem("D-003"),
            TestModels.CatalogItem("D-004"),
        });

        var plan = new ImportPlanBuilder().Build(document, catalog);

        Assert.Equal(new[] { "D-001" }, plan.Matches.Select(match => match.Item.ItemId));
        Assert.Equal(new[] { "D-002" }, plan.UnknownItems.Select(item => item.ItemId));
        Assert.Equal(new[] { "D-003" }, plan.SkippedItems.Select(item => item.ItemId));
        Assert.Equal(new[] { "D-004", "d-004" }, plan.DuplicateItems.Select(item => item.ItemId));
        Assert.True(plan.HasBlockingIssues);
    }

    [Fact]
    public void Catalog_RejectsDuplicateIdentifiersIgnoringCase()
    {
        var items = new[]
        {
            TestModels.CatalogItem("D-001"),
            TestModels.CatalogItem("d-001"),
        };

        var exception = Assert.Throws<ArgumentException>(() => new ContentCatalog(items));

        Assert.Contains("D-001", exception.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void ReviewSelection_AllowsOnlyCurrentActionableItems()
    {
        var document = TestModels.Document(
            TestModels.Item("D-001", selected: true),
            TestModels.Item("D-002", selected: true));
        var catalog = new ContentCatalog(new[]
        {
            TestModels.CatalogItem("D-001"),
            TestModels.CatalogItem("D-002"),
        });
        var review = new StartupImportReviewBuilder().Build(document, catalog, new[] { "D-002" });

        StartupImportSelection selection = review.CreateSelection(new[] { "d-001" });

        Assert.Equal(new[] { "d-001" }, selection.ItemIds);
        Assert.Equal(new[] { "D-001" }, selection.Resolve(review).Select(match => match.Item.ItemId));
        Assert.Throws<InvalidOperationException>(() => review.CreateSelection(new[] { "D-002" }));
    }
}
