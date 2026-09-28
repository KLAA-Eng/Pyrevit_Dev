using System;
using System.Collections.Generic;
using System.Globalization;
using System.Windows;
using KLCode.Wpf;

namespace KLCode.FamilyStudio.Revit.Views;

internal static class FamilyStudioText
{
    private static readonly IReadOnlyList<string> AvailableLocales =
        new[] { SupportedLocaleCatalog.FallbackLocale };

    internal static string Get(string key)
    {
        string locale = SupportedLocaleCatalog.SelectAvailableLocale(
            CultureInfo.CurrentUICulture.Name,
            AvailableLocales);
        string assemblyName = typeof(FamilyStudioText).Assembly.GetName().Name
            ?? throw new InvalidOperationException("The Family Studio assembly name is unavailable.");
        ResourceDictionary dictionary = new ResourceDictionary
        {
            Source = new Uri(
                "/" + assemblyName + ";component/Resources/Strings/ResourceDictionary." + locale + ".xaml",
                UriKind.RelativeOrAbsolute),
        };
        return dictionary[key] as string
            ?? throw new InvalidOperationException("The Family Studio string is missing: " + key);
    }

    internal static void ApplyToolStrings(ResourceDictionary resources)
    {
        ThemeBootstrapper.ApplyToolStrings(
            resources,
            CultureInfo.CurrentUICulture.Name,
            typeof(FamilyStudioText).Assembly,
            AvailableLocales,
            "Resources/Strings");
    }
}
