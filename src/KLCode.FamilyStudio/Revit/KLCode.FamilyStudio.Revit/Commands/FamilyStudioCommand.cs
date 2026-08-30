using System;
using System.IO;
using System.Linq;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using KLCode.FamilyStudio.Database.Repositories;
using KLCode.FamilyStudio.Revit.Services;
using KLCode.FamilyStudio.Revit.Views;

namespace KLCode.FamilyStudio.Revit.Commands;

[Transaction(TransactionMode.Manual)]
[Regeneration(RegenerationOption.Manual)]
public sealed class FamilyStudioCommand : IExternalCommand
{
    public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
    {
        UIDocument? uiDocument = commandData?.Application?.ActiveUIDocument;
        if (uiDocument is null || uiDocument.Document.IsFamilyDocument)
        {
            message = "Family Studio requires an active project document.";
            TaskDialog.Show("Family Studio", message);
            return Result.Cancelled;
        }

        try
        {
            string databasePath = GetDatabasePath();
            if (!File.Exists(databasePath))
            {
                string indexDirectory = Path.GetDirectoryName(databasePath) ?? string.Empty;
                string visibleFiles = Directory.Exists(indexDirectory)
                    ? string.Join(", ", Directory.GetFiles(indexDirectory).Select(Path.GetFileName))
                    : "<index folder is not visible>";
                TaskDialog.Show(
                    "Family Studio",
                    "No family index was found.\n\n" +
                    "Database path:\n" + databasePath +
                    "\n\nFiles visible in the Family Studio index folder:\n" +
                    visibleFiles);
                return Result.Cancelled;
            }

            using SqliteFamilyRepository repository = new SqliteFamilyRepository(databasePath);
            FamilyStudioWindow window = new FamilyStudioWindow(
                repository,
                new RevitFamilyLoadService(uiDocument));
            window.ShowDialog();
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
        string configuredPath = Environment.GetEnvironmentVariable("KLCODE_FAMILY_STUDIO_DATABASE");
        if (!string.IsNullOrWhiteSpace(configuredPath))
        {
            return configuredPath;
        }

        string applicationData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        return Path.Combine(applicationData, "KLCode", "FamilyStudio", "family_studio.sqlite");
    }
}
