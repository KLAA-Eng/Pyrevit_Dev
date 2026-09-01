using System;
using System.Collections.Generic;
using System.Reflection;
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

    /// <summary>
    /// Adds a tool-owned string dictionary after the common chrome resources.
    /// A missing requested locale deliberately falls back to the tool's English
    /// dictionary; it never selects a partially translated dictionary.
    /// </summary>
    public static void ApplyToolStrings(
        ResourceDictionary resources,
        string? requestedLocale,
        Assembly toolAssembly,
        IEnumerable<string> availableLocales,
        string resourceDirectory)
    {
        if (resources is null)
        {
            throw new ArgumentNullException(nameof(resources));
        }

        if (toolAssembly is null)
        {
            throw new ArgumentNullException(nameof(toolAssembly));
        }

        if (string.IsNullOrWhiteSpace(resourceDirectory))
        {
            throw new ArgumentException("A resource directory is required.", nameof(resourceDirectory));
        }

        string locale = SupportedLocaleCatalog.SelectAvailableLocale(
            requestedLocale,
            availableLocales);
        string assemblyName = toolAssembly.GetName().Name
            ?? throw new InvalidOperationException("The tool resource assembly name is unavailable.");
        string directory = resourceDirectory.Trim('/');
        resources.MergedDictionaries.Add(new ResourceDictionary
        {
            Source = new Uri(
                "/" + assemblyName + ";component/" + directory +
                "/ResourceDictionary." + locale + ".xaml",
                UriKind.RelativeOrAbsolute),
        });
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
