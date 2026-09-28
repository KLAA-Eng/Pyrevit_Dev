using System;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using KLA.ModelStartupImporter.Core;
using KLA.ModelStartupImporter.UI;
using KLA.ModelStartupImporter.UI.Views;
using KLCode.Wpf.Views;

namespace KLA.ModelStartupImporter.Revit;

[Transaction(TransactionMode.Manual)]
[Regeneration(RegenerationOption.Manual)]
public sealed class StartupImportCommand : IExternalCommand
{
    public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
    {
        if (commandData?.Application?.ActiveUIDocument?.Document == null)
        {
            message = StartupImporterText.Get("OpenProjectFirstLabel");
            KlaAlertWindow.ShowWarning(
                null,
                StartupImporterText.Get("StartupImporterTitle"),
                StartupImporterText.Get("ChecklistReadFailedHeading"),
                message);
            return Result.Cancelled;
        }

        Document destinationDocument = commandData.Application.ActiveUIDocument.Document;
        StartupSourcePickerWindow picker = new StartupSourcePickerWindow(destinationDocument.Title);
        if (picker.ShowDialog() != true)
        {
            return Result.Cancelled;
        }

        return ReviewAndImport(
            picker.ValidatedDocument ?? new StartupDocumentReader().Read(picker.ChecklistPath),
            picker.ValidatedSettings ?? new JsonStartupSettingsProvider().Load(picker.SettingsPath),
            commandData.Application.Application,
            destinationDocument,
            ref message);
    }

    private static Result ReviewAndImport(
        StartupDocumentModel startupDocument,
        StartupImportSettings settings,
        Autodesk.Revit.ApplicationServices.Application application,
        Document destinationDocument,
        ref string message)
    {
        try
        {
            var importer = new RevitStartupImportService(application);
            var review = importer.Review(startupDocument, settings, destinationDocument);
            if (review.Plan.HasBlockingIssues)
            {
                new BlockingIssuesWindow(settings, review).ShowDialog();
                return Result.Cancelled;
            }

            StartupImportReviewWindow reviewWindow = new StartupImportReviewWindow(
                startupDocument,
                settings,
                review);
            if (reviewWindow.ShowDialog() != true)
            {
                return Result.Cancelled;
            }

            StartupImportSelection selection = review.CreateSelection(reviewWindow.SelectedItemIds);
            importer.Import(startupDocument, settings, selection, destinationDocument);
            KlaAlertWindow.ShowInformation(
                null,
                StartupImporterText.Get("StartupImporterTitle"),
                StartupImporterText.Get("ImportCompleteHeading"),
                string.Format(
                    StartupImporterText.Get("ImportCompleteFormat"),
                    selection.ItemIds.Count,
                    review.ExistingMatches.Count,
                    settings.CatalogVersion));

            return Result.Succeeded;
        }
        catch (Exception exception) when (IsExpectedInputFailure(exception))
        {
            message = StartupImporterText.Get("ChecklistReadFailedPrefix") + exception.Message;
            KlaAlertWindow.ShowWarning(
                null,
                StartupImporterText.Get("StartupImporterTitle"),
                StartupImporterText.Get("ChecklistReadFailedHeading"),
                message + "\n\n" + StartupImporterText.Get("NothingImportedLabel"));
            return Result.Failed;
        }
        catch (Exception exception)
        {
            message = exception.ToString();
            KlaAlertWindow.ShowWarning(
                null,
                StartupImporterText.Get("StartupImporterTitle"),
                StartupImporterText.Get("ChecklistReadFailedHeading"),
                StartupImporterText.Get("NothingImportedLabel"));
            return Result.Failed;
        }
    }

    private static bool IsExpectedInputFailure(Exception exception)
    {
        return exception is ArgumentException ||
               exception is System.IO.IOException ||
               exception is NotSupportedException ||
               exception is StartupSettingsException;
    }

}
