using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using KLA.ModelStartupImporter.Core;

namespace KLA.ModelStartupImporter.Revit;

public interface ISeedContentImporter
{
    StartupImportReview Review(
        StartupDocumentModel startupDocument,
        StartupImportSettings settings,
        Document destinationDocument);

    void Import(
        StartupImportSettings settings,
        StartupImportReview review,
        Document destinationDocument);

    void Import(
        StartupDocumentModel startupDocument,
        StartupImportSettings settings,
        StartupImportSelection selection,
        Document destinationDocument);
}

public sealed class RevitStartupImportService : ISeedContentImporter
{
    private readonly Autodesk.Revit.ApplicationServices.Application _application;
    private readonly ScheduleDefinitionTranslator _scheduleTranslator;

    public RevitStartupImportService(Autodesk.Revit.ApplicationServices.Application application)
    {
        _application = application ?? throw new ArgumentNullException(nameof(application));
        _scheduleTranslator = new ScheduleDefinitionTranslator();
    }

    public StartupImportReview Review(
        StartupDocumentModel startupDocument,
        StartupImportSettings settings,
        Document destinationDocument)
    {
        if (destinationDocument is null)
        {
            throw new ArgumentNullException(nameof(destinationDocument));
        }

        StartupImportReview review = new StartupImportReviewBuilder().Build(
            startupDocument,
            settings.Catalog,
            FindExistingItemIds(settings.Catalog, destinationDocument));
        if (review.Plan.HasBlockingIssues)
        {
            return review;
        }

        using Document seedDocument = _application.OpenDocumentFile(settings.SeedModelPath);
        ValidateSourceViews(seedDocument, review.ActionableMatches);
        return review;
    }

    public void Import(
        StartupImportSettings settings,
        StartupImportReview review,
        Document destinationDocument)
    {
        if (review is null)
        {
            throw new ArgumentNullException(nameof(review));
        }

        if (destinationDocument is null)
        {
            throw new ArgumentNullException(nameof(destinationDocument));
        }

        if (review.Plan.HasBlockingIssues)
        {
            throw new InvalidOperationException("Resolve unknown and duplicate selected checklist items before importing.");
        }

        if (review.ActionableMatches.Count == 0)
        {
            throw new InvalidOperationException("No selected catalog items are available to import.");
        }

        StartupImportSelection selection = review.CreateSelection(
            review.ActionableMatches.Select(match => match.Item.ItemId));
        ImportMatches(settings, selection.Resolve(review), destinationDocument);
    }

    public void Import(
        StartupDocumentModel startupDocument,
        StartupImportSettings settings,
        StartupImportSelection selection,
        Document destinationDocument)
    {
        if (startupDocument is null)
        {
            throw new ArgumentNullException(nameof(startupDocument));
        }

        if (settings is null)
        {
            throw new ArgumentNullException(nameof(settings));
        }

        if (selection is null)
        {
            throw new ArgumentNullException(nameof(selection));
        }

        StartupImportReview refreshedReview = Review(startupDocument, settings, destinationDocument);
        ImportMatches(settings, selection.Resolve(refreshedReview), destinationDocument);
    }

    private void ImportMatches(
        StartupImportSettings settings,
        IReadOnlyList<ImportMatch> matches,
        Document destinationDocument)
    {
        if (matches.Count == 0)
        {
            throw new InvalidOperationException("No selected catalog items are available to import.");
        }

        using Document seedDocument = _application.OpenDocumentFile(settings.SeedModelPath);
        ValidateSourceViews(seedDocument, matches);
        using TransactionGroup group = new TransactionGroup(destinationDocument, "KL&A Startup Import");
        group.Start();
        try
        {
            foreach (ImportMatch match in matches)
            {
                using Transaction transaction = new Transaction(destinationDocument, "Import " + match.CatalogItem.TargetName);
                transaction.Start();
                ImportMatchContent(seedDocument, destinationDocument, match.CatalogItem);
                transaction.Commit();
            }

            group.Assimilate();
        }
        catch
        {
            group.RollBack();
            throw;
        }
    }

    private static IEnumerable<string> FindExistingItemIds(ContentCatalog catalog, Document destinationDocument)
    {
        HashSet<string> existingNames = new HashSet<string>(
            new FilteredElementCollector(destinationDocument)
                .OfClass(typeof(View))
                .Cast<View>()
                .Where(view => !view.IsTemplate)
                .Select(view => view.Name),
            StringComparer.OrdinalIgnoreCase);
        return catalog.Items
            .Where(item => existingNames.Contains(item.TargetName))
            .Select(item => item.ItemId)
            .ToArray();
    }

    private static void ValidateSourceViews(Document seedDocument, IReadOnlyList<ImportMatch> matches)
    {
        foreach (ImportMatch match in matches)
        {
            CatalogItem item = match.CatalogItem;
            if (item.ContentType == StartupItemCategory.Detail || item.ContentType == StartupItemCategory.GeneralNote)
            {
                if (FindDraftingView(seedDocument, item.SourceViewName) is null)
                {
                    throw new InvalidOperationException("The seed model does not contain drafting view '" + item.SourceViewName + "'.");
                }
            }
            else if (item.ContentType == StartupItemCategory.Schedule)
            {
                if (FindSchedule(seedDocument, item.SourceViewName) is null)
                {
                    throw new InvalidOperationException("The seed model does not contain schedule '" + item.SourceViewName + "'.");
                }
            }
            else
            {
                throw new NotSupportedException("Startup Importer cannot import content type '" + item.ContentType + "'.");
            }
        }
    }

    private void ImportMatchContent(Document seedDocument, Document destinationDocument, CatalogItem item)
    {
        if (item.ContentType == StartupItemCategory.Detail || item.ContentType == StartupItemCategory.GeneralNote)
        {
            ViewDrafting sourceView = FindDraftingView(seedDocument, item.SourceViewName)!;
            ViewDrafting destinationView = ViewDrafting.Create(destinationDocument, sourceView.GetTypeId());
            destinationView.Name = item.TargetName;
            ICollection<ElementId> sourceElementIds = new FilteredElementCollector(seedDocument, sourceView.Id)
                .WhereElementIsNotElementType()
                .ToElementIds();
            if (sourceElementIds.Count > 0)
            {
                ElementTransformUtils.CopyElements(
                    sourceView,
                    sourceElementIds,
                    destinationView,
                    Transform.Identity,
                    new CopyPasteOptions());
            }

            return;
        }

        if (item.ContentType == StartupItemCategory.Schedule)
        {
            _scheduleTranslator.Copy(FindSchedule(seedDocument, item.SourceViewName)!, destinationDocument, item.TargetName);
            return;
        }

        throw new NotSupportedException("Startup Importer cannot import content type '" + item.ContentType + "'.");
    }

    private static ViewDrafting? FindDraftingView(Document document, string name)
    {
        return new FilteredElementCollector(document)
            .OfClass(typeof(ViewDrafting))
            .Cast<ViewDrafting>()
            .FirstOrDefault(view => string.Equals(view.Name, name, StringComparison.OrdinalIgnoreCase));
    }

    private static ViewSchedule? FindSchedule(Document document, string name)
    {
        return new FilteredElementCollector(document)
            .OfClass(typeof(ViewSchedule))
            .Cast<ViewSchedule>()
            .FirstOrDefault(view => !view.IsTemplate && string.Equals(view.Name, name, StringComparison.OrdinalIgnoreCase));
    }
}

public sealed class ScheduleDefinitionTranslator
{
    public ViewSchedule Copy(ViewSchedule sourceSchedule, Document destinationDocument, string targetName)
    {
        if (sourceSchedule is null)
        {
            throw new ArgumentNullException(nameof(sourceSchedule));
        }

        if (destinationDocument is null)
        {
            throw new ArgumentNullException(nameof(destinationDocument));
        }

        if (string.IsNullOrWhiteSpace(targetName))
        {
            throw new ArgumentException("A target schedule name is required.", nameof(targetName));
        }

        ScheduleDefinition source = sourceSchedule.Definition;
        if (source.IsKeySchedule || source.IsMaterialTakeoff || source.HasEmbeddedSchedule)
        {
            throw new NotSupportedException("Key schedules, material takeoffs, and embedded schedules are not supported in this wave.");
        }

        ViewSchedule destination = ViewSchedule.CreateSchedule(destinationDocument, source.CategoryId);
        destination.Name = targetName.Trim();
        Dictionary<ScheduleFieldId, ScheduleFieldId> fieldMap = CopyFields(source, destination.Definition);
        CopySortGroups(source, destination.Definition, fieldMap);
        CopyStringFilters(source, destination.Definition, fieldMap);
        return destination;
    }

    private static Dictionary<ScheduleFieldId, ScheduleFieldId> CopyFields(ScheduleDefinition source, ScheduleDefinition destination)
    {
        Dictionary<ScheduleFieldId, ScheduleFieldId> map = new Dictionary<ScheduleFieldId, ScheduleFieldId>();
        foreach (ScheduleFieldId sourceId in source.GetFieldOrder())
        {
            ScheduleField sourceField = source.GetField(sourceId);
            if (sourceField.IsCalculatedField || sourceField.IsCombinedParameterField)
            {
                throw new NotSupportedException("Calculated and combined schedule fields are not supported in this wave.");
            }

            ScheduleField destinationField = destination.AddField(sourceField.FieldType, sourceField.ParameterId);
            destinationField.ColumnHeading = sourceField.ColumnHeading;
            destinationField.GridColumnWidth = sourceField.GridColumnWidth;
            map.Add(sourceId, destinationField.FieldId);
        }

        return map;
    }

    private static void CopySortGroups(
        ScheduleDefinition source,
        ScheduleDefinition destination,
        IReadOnlyDictionary<ScheduleFieldId, ScheduleFieldId> fieldMap)
    {
        foreach (ScheduleSortGroupField sourceSort in source.GetSortGroupFields())
        {
            if (!fieldMap.TryGetValue(sourceSort.FieldId, out ScheduleFieldId? destinationId))
            {
                throw new NotSupportedException("The schedule has an unsupported sorting/grouping field.");
            }

            ScheduleSortGroupField destinationSort = new ScheduleSortGroupField(destinationId, sourceSort.SortOrder)
            {
                ShowBlankLine = sourceSort.ShowBlankLine,
                ShowFooter = sourceSort.ShowFooter,
                ShowFooterCount = sourceSort.ShowFooterCount,
                ShowFooterTitle = sourceSort.ShowFooterTitle,
                ShowHeader = sourceSort.ShowHeader,
            };
            destination.AddSortGroupField(destinationSort);
        }
    }

    private static void CopyStringFilters(
        ScheduleDefinition source,
        ScheduleDefinition destination,
        IReadOnlyDictionary<ScheduleFieldId, ScheduleFieldId> fieldMap)
    {
        foreach (ScheduleFilter sourceFilter in source.GetFilters())
        {
            if (!fieldMap.TryGetValue(sourceFilter.FieldId, out ScheduleFieldId? destinationId))
            {
                throw new NotSupportedException("The schedule has an unsupported filter field.");
            }

            try
            {
                destination.AddFilter(new ScheduleFilter(destinationId, sourceFilter.FilterType, sourceFilter.GetStringValue()));
            }
            catch (InvalidOperationException exception)
            {
                throw new NotSupportedException("Only string-valued schedule filters are supported in this wave.", exception);
            }
        }
    }
}
