using System;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using KLCode.FamilyStudio.Core.Search;

namespace KLCode.FamilyStudio.Revit.Services;

internal sealed class RevitFamilyLoadService : IFamilyLoadService
{
    private readonly UIDocument _uiDocument;

    public RevitFamilyLoadService(UIDocument uiDocument)
    {
        _uiDocument = uiDocument ?? throw new ArgumentNullException(nameof(uiDocument));
    }

    public void Load(FamilySearchResult family)
    {
        GetOrLoadFamily(family);
    }

    public void LoadAndPlace(FamilySearchResult family)
    {
        Family loadedFamily = GetOrLoadFamily(family);
        FamilySymbol symbol = loadedFamily.GetFamilySymbolIds()
            .Select(id => _uiDocument.Document.GetElement(id))
            .OfType<FamilySymbol>()
            .FirstOrDefault()
            ?? throw new InvalidOperationException("The selected family has no placeable types.");
        Activate(symbol);
        _uiDocument.PromptForFamilyInstancePlacement(symbol);
    }

    private Family GetOrLoadFamily(FamilySearchResult family)
    {
        if (family is null)
        {
            throw new ArgumentNullException(nameof(family));
        }

        Document document = _uiDocument.Document;
        Family? loadedFamily;
        TransactionStatus status;
        using (Transaction transaction = new Transaction(document, "Load Family Studio Family"))
        {
            transaction.Start();
            bool loaded = document.LoadFamily(family.FilePath, new KlaFamilyLoadOptions(), out loadedFamily);
            status = transaction.Commit();
            if (loaded && loadedFamily is not null && status == TransactionStatus.Committed)
            {
                return loadedFamily;
            }
        }

        Family? existingFamily = new FilteredElementCollector(document)
            .OfClass(typeof(Family))
            .Cast<Family>()
            .FirstOrDefault(candidate => string.Equals(
                candidate.Name,
                family.FamilyName,
                StringComparison.OrdinalIgnoreCase));
        if (existingFamily is not null)
        {
            return existingFamily;
        }

        throw new InvalidOperationException("Revit did not load the selected family into the project.");
    }

    private void Activate(FamilySymbol symbol)
    {
        if (symbol.IsActive)
        {
            return;
        }

        using Transaction transaction = new Transaction(_uiDocument.Document, "Activate Family Type");
        transaction.Start();
        symbol.Activate();
        _uiDocument.Document.Regenerate();
        transaction.Commit();
    }

}
