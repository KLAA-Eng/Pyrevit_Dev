using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace KLA.ModelStartupImporter.Core;

public sealed class ContentCatalog
{
    private readonly IReadOnlyDictionary<string, CatalogItem> itemsById;
    private readonly IReadOnlyCollection<CatalogItem> items;

    public ContentCatalog(IEnumerable<CatalogItem> items)
    {
        if (items == null)
        {
            throw new ArgumentNullException(nameof(items));
        }

        var copy = items.ToList();
        if (copy.Any(item => item == null))
        {
            throw new ArgumentException("Catalog items cannot contain null values.", nameof(items));
        }

        var duplicateId = copy
            .GroupBy(item => item.ItemId, StringComparer.OrdinalIgnoreCase)
            .FirstOrDefault(group => group.Count() > 1)?.Key;
        if (duplicateId != null)
        {
            throw new ArgumentException("The catalog contains duplicate item id '" + duplicateId + "'.", nameof(items));
        }

        var dictionary = copy.ToDictionary(item => item.ItemId, StringComparer.OrdinalIgnoreCase);
        itemsById = new ReadOnlyDictionary<string, CatalogItem>(dictionary);
        this.items = new ReadOnlyCollection<CatalogItem>(copy);
    }

    public IReadOnlyCollection<CatalogItem> Items => items;

    public bool TryGet(string itemId, out CatalogItem? item)
    {
        if (string.IsNullOrWhiteSpace(itemId))
        {
            item = null;
            return false;
        }

        return itemsById.TryGetValue(itemId.Trim(), out item);
    }
}
