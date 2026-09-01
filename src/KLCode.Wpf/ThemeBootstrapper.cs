using System;
using System.Collections.Generic;
using System.Windows;

namespace KLCode.Wpf;

public static class ThemeBootstrapper
{
    private static readonly IReadOnlyList<string> AvailableLocales =
        new[] { SupportedLocaleCatalog.FallbackLocale };

    public static void Apply(ResourceDictionary resources, string? requestedLocale)
    {
        if (resources is null)
        {
            throw new ArgumentNullException(nameof(resources));
        }

        string locale = SupportedLocaleCatalog.SelectAvailableLocale(
            requestedLocale,
            AvailableLocales);
        resources.MergedDictionaries.Add(Load("Resources/KLCodeControls.xaml"));
        resources.MergedDictionaries.Add(
            Load("Resources/Strings/ResourceDictionary." + locale + ".xaml"));
    }

    private static ResourceDictionary Load(string componentPath)
    {
        string assemblyName = typeof(ThemeBootstrapper).Assembly.GetName().Name
            ?? throw new InvalidOperationException("The WPF adapter assembly name is unavailable.");
        return new ResourceDictionary
        {
            Source = new Uri(
                "/" + assemblyName + ";component/" + componentPath,
                UriKind.RelativeOrAbsolute),
        };
    }
}
