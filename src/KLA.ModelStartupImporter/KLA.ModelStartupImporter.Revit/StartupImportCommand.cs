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

        return ShowPreflight(dialog.FileName, ref message);
    }

    private static Result ShowPreflight(string sourcePath, ref string message)
    {
        try
        {
            var startupDocument = new StartupDocumentReader().Read(sourcePath);
            var selectedCount = startupDocument.Items.Count(item => item.IsSelected);
            var skippedCount = startupDocument.Items.Count - selectedCount;
            var summary =
                "Preflight complete. No Revit model changes were made.\n\n" +
                "Selected items: " + selectedCount + "\n" +
                "Unchecked items: " + skippedCount + "\n" +
                "File SHA-256: " + startupDocument.FileHash + "\n\n" +
                "Catalog, seed-model import, and link updates remain disabled until their project contracts are configured and live-tested.";
            TaskDialog.Show("KL&A Startup Importer", summary);
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
               exception is NotSupportedException;
    }
}
