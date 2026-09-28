using System;
using System.Collections.Generic;
using System.Globalization;
using System.Windows;
using KLCode.Wpf;

namespace KLA.ModelStartupImporter.UI;

public static class StartupImporterText
{
    private static readonly IReadOnlyList<string> AvailableLocales =
        new[] { SupportedLocaleCatalog.FallbackLocale };

    public static string Get(string key)
    {
        if (string.IsNullOrWhiteSpace(key))
        {
            throw new ArgumentException("A resource key is required.", nameof(key));
        }

        string locale = SupportedLocaleCatalog.SelectAvailableLocale(
            CultureInfo.CurrentUICulture.Name,
            AvailableLocales);
        string assemblyName = typeof(StartupImporterText).Assembly.GetName().Name
            ?? throw new InvalidOperationException("The Startup Importer UI assembly name is unavailable.");
        ResourceDictionary dictionary = new ResourceDictionary
        {
            Source = new Uri(
                "/" + assemblyName + ";component/Resources/Strings/ResourceDictionary." + locale + ".xaml",
                UriKind.RelativeOrAbsolute),
        };
        return dictionary[key] as string
            ?? throw new InvalidOperationException("The Startup Importer string is missing: " + key);
    }

    internal static void ApplyToolStrings(ResourceDictionary resources)
    {
        ThemeBootstrapper.ApplyToolStrings(
            resources,
            CultureInfo.CurrentUICulture.Name,
            typeof(StartupImporterText).Assembly,
            AvailableLocales,
            "Resources/Strings");
    }
}
