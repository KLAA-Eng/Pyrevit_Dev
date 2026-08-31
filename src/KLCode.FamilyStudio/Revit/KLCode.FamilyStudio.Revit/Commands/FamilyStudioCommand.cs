using System;
using System.IO;
using System.Threading;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using KLCode.FamilyStudio.Database.Repositories;
using KLCode.FamilyStudio.Revit.Services;
using KLCode.FamilyStudio.Revit.Views;
using Microsoft.Win32;

namespace KLCode.FamilyStudio.Revit.Commands;

[Transaction(TransactionMode.Manual)]
[Regeneration(RegenerationOption.Manual)]
public sealed class FamilyStudioCommand : IExternalCommand
{
    public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
    {
        UIApplication? revitApplication = commandData?.Application;
        UIDocument? uiDocument = revitApplication?.ActiveUIDocument;
        if (revitApplication is null || uiDocument is null || uiDocument.Document.IsFamilyDocument)
        {
            message = "Family Studio requires an active project document.";
            TaskDialog.Show("Family Studio", message);
            return Result.Cancelled;
        }

        try
        {
            string databasePath = GetDatabasePath();
            using SqliteFamilyRepository repository = new SqliteFamilyRepository(databasePath);
            RevitFamilyLoadService loadService = new RevitFamilyLoadService(uiDocument);
            FamilyStudioWindow window = new FamilyStudioWindow(
                repository,
                loadService,
                () => RefreshLibrary(revitApplication.Application, databasePath));
            window.ShowDialog();

            if (window.PlacementFamily is not null)
            {
                try
                {
                    loadService.LoadAndPlace(window.PlacementFamily);
                    repository.RecordUse(window.PlacementFamily.Id, KLCode.FamilyStudio.Core.Search.FamilyUseAction.Placed, DateTimeOffset.UtcNow);
                }
                catch (Autodesk.Revit.Exceptions.OperationCanceledException)
                {
                    // Esc ends Revit's placement prompt without creating an
                    // instance. It is an expected user action, not an error.
                }
            }

            return Result.Succeeded;
        }
        catch (Exception exception)
        {
            message = "Family Studio could not open:\n\n" + exception;
            TaskDialog.Show("Family Studio", message);
            return Result.Cancelled;
        }
    }

    private static string GetDatabasePath()
    {
        string? configuredPath = Environment.GetEnvironmentVariable("KLCODE_FAMILY_STUDIO_DATABASE");
        if (!string.IsNullOrWhiteSpace(configuredPath))
        {
            return configuredPath;
        }

        string applicationData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        return Path.Combine(applicationData, "KLCode", "FamilyStudio", "family_studio.sqlite");
    }

    private static KLCode.FamilyStudio.Core.Indexing.IndexRunSummary? RefreshLibrary(
        Autodesk.Revit.ApplicationServices.Application application,
        string databasePath)
    {
        OpenFileDialog dialog = new OpenFileDialog
        {
            Title = "Select Family Studio library configuration",
            Filter = "Family Studio configuration (*.json)|*.json",
            CheckFileExists = true,
            Multiselect = false,
        };
        if (dialog.ShowDialog() != true)
        {
            return null;
        }

        return new RevitLibraryIndexService(application).Refresh(dialog.FileName, databasePath, CancellationToken.None);
    }
}
