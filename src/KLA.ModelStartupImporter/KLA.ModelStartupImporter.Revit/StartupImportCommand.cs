using System;
using System.Linq;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using KLA.ModelStartupImporter.Core;
using Microsoft.Win32;

namespace KLA.ModelStartupImporter.Revit;

[Transaction(TransactionMode.Manual)]
[Regeneration(RegenerationOption.Manual)]
public sealed class StartupImportCommand : IExternalCommand
{
    public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
    {
        if (commandData?.Application?.ActiveUIDocument?.Document == null)
        {
            message = "Open a Revit project before running Startup Importer.";
            return Result.Cancelled;
        }

        var dialog = new OpenFileDialog
        {
            Title = "Select a KL&A startup checklist",
            Filter = "Startup checklists (*.docx;*.xlsx)|*.docx;*.xlsx",
            CheckFileExists = true,
            Multiselect = false,
        };
        if (dialog.ShowDialog() != true)
        {
            return Result.Cancelled;
        }

        var settingsDialog = new OpenFileDialog
        {
            Title = "Select Startup Importer settings",
            Filter = "Startup Importer settings (*.json)|*.json",
            CheckFileExists = true,
            Multiselect = false,
        };
        if (settingsDialog.ShowDialog() != true)
        {
            return Result.Cancelled;
        }

        return ReviewAndImport(
            dialog.FileName,
            settingsDialog.FileName,
            commandData.Application.Application,
            commandData.Application.ActiveUIDocument.Document,
            ref message);
    }

    private static Result ReviewAndImport(
        string sourcePath,
        string settingsPath,
        Autodesk.Revit.ApplicationServices.Application application,
        Document destinationDocument,
        ref string message)
    {
        try
        {
            var startupDocument = new StartupDocumentReader().Read(sourcePath);
            var settings = new JsonStartupSettingsProvider().Load(settingsPath);
            var importer = new RevitStartupImportService(application);
            var review = importer.Review(startupDocument, settings, destinationDocument);
            var dialog = new TaskDialog("KL&A Startup Importer Review")
            {
                MainInstruction = review.Plan.HasBlockingIssues
                    ? "Resolve the checklist issues before importing."
                    : review.ActionableMatches.Count == 0
                        ? "No new selected items are available to import."
                        : "Review the startup content before importing.",
                MainContent = BuildReviewSummary(startupDocument, settings, review),
                CommonButtons = review.CanImport ? TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No : TaskDialogCommonButtons.Close,
                DefaultButton = review.CanImport ? TaskDialogResult.No : TaskDialogResult.Close,
            };
            if (dialog.Show() == TaskDialogResult.Yes)
            {
                importer.Import(settings, review, destinationDocument);
                TaskDialog.Show(
                    "KL&A Startup Importer",
                    "Import complete. Created items: " + review.ActionableMatches.Count +
                    "\nSkipped existing items: " + review.ExistingMatches.Count +
                    "\nCatalog version: " + settings.CatalogVersion);
            }

            return Result.Succeeded;
        }
        catch (Exception exception) when (IsExpectedInputFailure(exception))
        {
            message = "The startup checklist could not be read: " + exception.Message;
            TaskDialog.Show("KL&A Startup Importer", message);
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

    private static string BuildReviewSummary(
        StartupDocumentModel startupDocument,
        StartupImportSettings settings,
        StartupImportReview review)
    {
        return "Selected: " + startupDocument.Items.Count(item => item.IsSelected) + "\n" +
               "Unchecked: " + review.Plan.SkippedItems.Count + "\n" +
               "Matched for import: " + review.ActionableMatches.Count + "\n" +
               "Already present (skipped): " + review.ExistingMatches.Count + "\n" +
               "Unknown (blocking): " + review.Plan.UnknownItems.Count + "\n" +
               "Duplicate (blocking): " + review.Plan.DuplicateItems.Count + "\n" +
               "Catalog version: " + settings.CatalogVersion + "\n" +
               "Seed model: " + settings.SeedModelPath + "\n" +
               "Checklist SHA-256: " + startupDocument.FileHash;
    }
}
