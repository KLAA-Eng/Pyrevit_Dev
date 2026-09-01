using System.Text.RegularExpressions;
using System.Xml.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace KLCode.Wpf.Source.Tests;

[TestClass]
public sealed class DesignSystemResourceContractTests
{
    private static readonly string[] RequiredPaletteKeys =
    {
        "header_background",
        "text_white",
        "text_gray",
        "text_green",
        "button_fg_normal",
        "button_bg_normal",
        "button_bg_hover",
        "border_green_dark",
        "border_green",
        "uncheckbox_checked_colour",
        "checkbox_checked_colour",
        "footer_donate",
    };

    private static readonly string[] RequiredSmokeCopyKeys =
    {
        "DesignSystemSmokeTitle",
        "BrandSlash",
        "BrandName",
        "CloseLabel",
        "DesignSystemSmokeBody",
        "PrototypeLabel",
        "VersionLabel",
        "OutreachLabel",
    };

    private static readonly XNamespace Presentation =
        "http://schemas.microsoft.com/winfx/2006/xaml/presentation";

    private static readonly XNamespace Xaml =
        "http://schemas.microsoft.com/winfx/2006/xaml";

    [TestMethod]
    public void CanonicalPalette_DefinesRequiredKeysWithoutEventHandlers()
    {
        XDocument palette = LoadXaml("lib/GUI/Resources/KLCode_palette.xaml");
        HashSet<string> keys = palette
            .Descendants()
            .Select(element => (string?)element.Attribute(Xaml + "Key"))
            .Where(key => key is not null)
            .Select(key => key!)
            .ToHashSet(StringComparer.Ordinal);

        CollectionAssert.IsSubsetOf(RequiredPaletteKeys, keys.ToArray());
        Assert.IsFalse(
            palette.Descendants().Attributes().Any(IsEventAttribute),
            "The canonical palette must remain data-only so compiled WPF can load it.");
    }

    [TestMethod]
    public void LegacyStyles_MergeTheCanonicalPaletteInsteadOfForkingBrushes()
    {
        XDocument legacyStyles = LoadXaml("lib/GUI/Resources/WPF_styles.xaml");
        string[] mergedSources = legacyStyles
            .Descendants(Presentation + "ResourceDictionary")
            .Attributes("Source")
            .Select(attribute => attribute.Value)
            .ToArray();

        CollectionAssert.Contains(mergedSources, "KLCode_palette.xaml");
        Assert.AreEqual(
            0,
            legacyStyles.Root!.Elements(Presentation + "SolidColorBrush").Count(),
            "Palette brushes must have one canonical definition.");
    }

    [TestMethod]
    public void CompiledAdapter_UsesCanonicalResourcesAndLocalizedCopy()
    {
        XDocument controls = LoadXaml("src/KLCode.Wpf/Resources/KLCodeControls.xaml");
        XDocument smokeWindow = LoadXaml("src/KLCode.Wpf/Views/DesignSystemSmokeWindow.xaml");
        XDocument english = LoadXaml(
            "src/KLCode.Wpf/Resources/Strings/ResourceDictionary.en_us.xaml");

        AssertNoColorLiterals(controls, "compiled control resources");
        AssertNoColorLiterals(smokeWindow, "compiled smoke window");

        HashSet<string> copyKeys = english
            .Descendants()
            .Select(element => (string?)element.Attribute(Xaml + "Key"))
            .Where(key => key is not null)
            .Select(key => key!)
            .ToHashSet(StringComparer.Ordinal);
        CollectionAssert.IsSubsetOf(RequiredSmokeCopyKeys, copyKeys.ToArray());

        foreach (XAttribute attribute in smokeWindow.Descendants().Attributes())
        {
            if (attribute.Name.LocalName is "Content" or "Text" or "Title" or "ToolTip")
            {
                StringAssert.StartsWith(attribute.Value, "{StaticResource ");
            }
        }
    }

    [TestMethod]
    public void RevitConsumers_ReferenceTheAdapterAndExposeTheSmokeCommand()
    {
        AssertProjectReferencesAdapter(
            "src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/" +
            "KLCode.FamilyStudio.Revit.csproj");
        AssertProjectReferencesAdapter(
            "src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Revit/" +
            "KLA.ModelStartupImporter.Revit.csproj");

        string commandPath = Path.Combine(
            FindRepositoryRoot(),
            "src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/" +
            "Commands/DesignSystemSmokeCommand.cs");
        Assert.IsTrue(File.Exists(commandPath), "The Revit-hosted smoke command is missing.");
        string command = File.ReadAllText(commandPath);
        StringAssert.Contains(command, "DesignSystemSmokeWindow");
        StringAssert.Contains(command, "CurrentUICulture.Name");
    }

    [TestMethod]
    public void HostPackaging_PreservesBothAdaptersAndUsesResolvablePackUris()
    {
        XDocument adapterProject = XDocument.Load(Path.Combine(
            FindRepositoryRoot(),
            "src/KLCode.Wpf/KLCode.Wpf.csproj"));
        string[] net48AssemblyNames = adapterProject
            .Descendants("PropertyGroup")
            .Where(group => ((string?)group.Attribute("Condition"))?.Contains(
                "net48",
                StringComparison.Ordinal) == true)
            .Elements("AssemblyName")
            .Select(element => element.Value)
            .ToArray();
        CollectionAssert.Contains(net48AssemblyNames, "KLCode.Wpf_2024");

        XDocument controls = LoadXaml("src/KLCode.Wpf/Resources/KLCodeControls.xaml");
        string[] mergedSources = controls
            .Descendants(Presentation + "ResourceDictionary")
            .Attributes("Source")
            .Select(attribute => attribute.Value)
            .ToArray();
        CollectionAssert.Contains(mergedSources, "KLCodePalette.xaml");

        string bootstrapper = File.ReadAllText(Path.Combine(
            FindRepositoryRoot(),
            "src/KLCode.Wpf/ThemeBootstrapper.cs"));
        StringAssert.Contains(bootstrapper, "Assembly.GetName().Name");

        string familyProject = File.ReadAllText(Path.Combine(
            FindRepositoryRoot(),
            "src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/" +
            "KLCode.FamilyStudio.Revit.csproj"));
        StringAssert.Contains(familyProject, "KLCode.Wpf_2024.dll");
        StringAssert.Contains(familyProject, "KLCode.Wpf.dll");
        StringAssert.Contains(familyProject, "Design System Smoke.invokebutton/bin");

        string startupPackaging = File.ReadAllText(Path.Combine(
            FindRepositoryRoot(),
            "src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Packaging.proj"));
        StringAssert.Contains(startupPackaging, "KLCode.Wpf_2024.dll");
        StringAssert.Contains(startupPackaging, "KLCode.Wpf.dll");
    }

    private static XDocument LoadXaml(string relativePath)
    {
        string path = Path.Combine(FindRepositoryRoot(), relativePath);
        Assert.IsTrue(File.Exists(path), "Required design-system file is missing: " + relativePath);
        return XDocument.Load(path, LoadOptions.SetLineInfo);
    }

    private static string FindRepositoryRoot()
    {
        DirectoryInfo? directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "AGENTS.md")) &&
                Directory.Exists(Path.Combine(directory.FullName, "lib", "GUI", "Resources")))
            {
                return directory.FullName;
            }

            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException("Could not locate the KLCode.pyRevit repository root.");
    }

    private static bool IsEventAttribute(XAttribute attribute)
    {
        return attribute.Name.Namespace == XNamespace.None &&
               attribute.Name.LocalName is "Click" or "Loaded" or "MouseLeftButtonDown";
    }

    private static void AssertNoColorLiterals(XDocument document, string surface)
    {
        string serialized = document.ToString(SaveOptions.DisableFormatting);
        Assert.IsFalse(
            Regex.IsMatch(serialized, "#[0-9A-Fa-f]{6,8}", RegexOptions.CultureInvariant),
            surface + " must reference canonical palette resources instead of color literals.");
    }

    private static void AssertProjectReferencesAdapter(string relativePath)
    {
        XDocument project = XDocument.Load(Path.Combine(FindRepositoryRoot(), relativePath));
        string[] references = project
            .Descendants("ProjectReference")
            .Select(element => (string?)element.Attribute("Include"))
            .Where(include => include is not null)
            .Select(include => include!.Replace('\\', '/'))
            .ToArray();

        Assert.IsTrue(
            references.Any(reference => reference.EndsWith(
                "/KLCode.Wpf/KLCode.Wpf.csproj",
                StringComparison.Ordinal)),
            relativePath + " must reference the shared compiled-WPF adapter.");
    }
}
