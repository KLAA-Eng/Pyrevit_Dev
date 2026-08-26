using System;
using System.Collections.Generic;
using System.Linq;

namespace KLA.ModelStartupImporter.Core;

public sealed class ImportPlanBuilder
{
    public ImportPlan Build(StartupDocumentModel document, ContentCatalog catalog)
    {
        if (document == null)
        {
            throw new ArgumentNullException(nameof(document));
        }

        if (catalog == null)
        {
            throw new ArgumentNullException(nameof(catalog));
        }

        var selected = document.Items.Where(item => item.IsSelected).ToList();
        var duplicateIds = new HashSet<string>(
            selected
                .GroupBy(item => item.ItemId, StringComparer.OrdinalIgnoreCase)
                .Where(group => group.Count() > 1)
                .Select(group => group.Key),
            StringComparer.OrdinalIgnoreCase);
        var duplicates = selected.Where(item => duplicateIds.Contains(item.ItemId)).ToList();
        var candidates = selected.Where(item => !duplicateIds.Contains(item.ItemId)).ToList();
        var matches = new List<ImportMatch>();
        var unknown = new List<StartupItem>();

        foreach (var item in candidates)
        {
            if (catalog.TryGet(item.ItemId, out var catalogItem) && catalogItem != null)
            {
                matches.Add(new ImportMatch(item, catalogItem));
            }
            else
            {
                unknown.Add(item);
            }
        }

        return new ImportPlan(
            matches,
            document.Items.Where(item => !item.IsSelected),
            unknown,
            duplicates);
    }
}
