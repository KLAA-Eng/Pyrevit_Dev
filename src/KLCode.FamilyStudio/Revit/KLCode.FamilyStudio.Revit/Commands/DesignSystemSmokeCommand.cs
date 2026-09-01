using System;
using System.Globalization;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using KLCode.Wpf.Views;

namespace KLCode.FamilyStudio.Revit.Commands;

[Transaction(TransactionMode.Manual)]
[Regeneration(RegenerationOption.Manual)]
public sealed class DesignSystemSmokeCommand : IExternalCommand
{
    public Result Execute(
        ExternalCommandData commandData,
        ref string message,
        ElementSet elements)
    {
        try
        {
            DesignSystemSmokeWindow window = new DesignSystemSmokeWindow(
                CultureInfo.CurrentUICulture.Name);
            window.ShowDialog();
            return Result.Succeeded;
        }
        catch (Exception exception)
        {
            message = exception.Message;
            return Result.Failed;
        }
    }
}
