using KLA.ModelStartupImporter.Core;

namespace KLA.ModelStartupImporter.Tests;

internal static class TestModels
{
    public static StartupItem Item(string itemId, bool selected)
    {
        return new StartupItem(itemId, itemId, StartupItemCategory.Detail, selected, string.Empty, "fixture", string.Empty);
    }

    public static StartupDocumentModel Document(params StartupItem[] items)
    {
        return new StartupDocumentModel(
            "/fixtures/startup.docx",
            StartupSourceType.Word,
            new DateTime(2026, 1, 2, 3, 4, 5, DateTimeKind.Utc),
            new string('A', 64),
            items);
    }

    public static CatalogItem CatalogItem(string itemId)
    {
        return new CatalogItem(itemId, itemId + " source", itemId + " target", StartupItemCategory.Detail);
    }
}
