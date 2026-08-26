using System;
using System.IO;
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
            return Result.Cancelled;
        }

        try
        {
            string databasePath = GetDatabasePath();
            if (!File.Exists(databasePath))
            {
                TaskDialog.Show("Family Studio", "No family index was found. Run the Family Studio indexer first.");
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
            message = "Family Studio could not open: " + exception.Message;
            return Result.Failed;
        }
    }

    private static string GetDatabasePath()
    {
        string localData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        return Path.Combine(localData, "KLCode", "FamilyStudio", "family_studio.sqlite");
    }
}
