using KLCode.FamilyStudio.Core.Search;

namespace KLCode.FamilyStudio.Revit.Services;

internal interface IFamilyLoadService
{
    void Load(FamilySearchResult family);
    void LoadAndPlace(FamilySearchResult family);
}
