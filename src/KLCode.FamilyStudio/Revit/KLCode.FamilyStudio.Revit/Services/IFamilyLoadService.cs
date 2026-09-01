using KLCode.FamilyStudio.Core.Search;
using System.Collections.Generic;

namespace KLCode.FamilyStudio.Revit.Services;

internal interface IFamilyLoadService
{
    void Load(FamilySearchResult family);
    void LoadAndPlace(FamilySearchResult family);
    void LoadBatch(IReadOnlyList<FamilySearchResult> families);
}
