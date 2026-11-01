using System.Text.RegularExpressions;
using System.Xml.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace KLCode.Wpf.Source.Tests;

[TestClass]
public sealed class DesignSystemResourceContractTests
{
    private static readonly string[] RequiredPaletteKeys =
    {
        "klcWindowColor",
        "klcTextColor",
        "KlaMutedBrush",
        "klcFooterLinkColor",
        "klcFooterVersionColor",
        "klcTextWatermarkColor",
        "KlaTextOnAccentBrush",
        "KlaAccentBrush",
        "KlaAccentHoverBrush",
        "klcBorderColor",
        "KlaBorderStrongBrush",
    };

    // The 2019 palette aliases were removed on 2026-10-31; consumers name the role brushes.
    private static readonly string[] RemovedPaletteAliases =
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
    };

    private static readonly string[] RequiredCompiledStyleKeys =
    {
        "KlaWindowStyle",
        "KlaButtonStyle",
        "KlaCloseButtonStyle",
        "KlaGhostButtonStyle",
        "KlaLinkButtonStyle",
        "KlaSegmentButtonStyle",
        "KlaTextBoxStyle",
        "KlaComboBoxStyle",
        "KlaCheckBoxStyle",
        "KlaListBoxStyle",
        "KlaListBoxItemStyle",
        "KlaGroupBorderStyle",
        "KlaPreviewBorderStyle",
        "KlaGroupCaptionStyle",
        "KlaChipBorderStyle",
        "KlaInfoChipStyle",
        "KlaWarningChipStyle",
        "KlaBlockingChipStyle",
        "KlaNeutralChipStyle",
    };

    private static readonly XNamespace Presentation =
        "http://schemas.microsoft.com/winfx/2006/xaml/presentation";

    private static readonly XNamespace Xaml =
        "http://schemas.microsoft.com/winfx/2006/xaml";

    [TestMethod]
    public void CanonicalPalette_DefinesRequiredKeysWithoutEventHandlers()
    {
        XDocument palette = LoadXaml("lib/GUI/Resources/KLCodeTokens.xaml");
        HashSet<string> keys = palette
            .Descendants()
            .Select(element => (string?)element.Attribute(Xaml + "Key"))
            .Where(key => key is not null)
            .Select(key => key!)
            .ToHashSet(StringComparer.Ordinal);

        CollectionAssert.IsSubsetOf(RequiredPaletteKeys, keys.ToArray());
        foreach (string alias in RemovedPaletteAliases)
        {
            Assert.IsFalse(keys.Contains(alias), "Removed palette alias returned: " + alias);
        }
        HashSet<string> componentKeys = LoadXaml("lib/GUI/Resources/KLCodeComponents.xaml")
            .Descendants()
            .Select(element => (string?)element.Attribute(Xaml + "Key"))
            .Where(key => key is not null)
            .Select(key => key!)
            .ToHashSet(StringComparer.Ordinal);
        foreach (string alias in new[] { "KlaPanelBrush", "KlaMutedTextBrush", "KlaSubtleTextBrush", "KlaBlockingBrush" })
        {
            Assert.IsFalse(componentKeys.Contains(alias), "Removed compiled-host brush alias returned: " + alias);
        }
        Assert.IsFalse(
            palette.Descendants().Attributes().Any(IsEventAttribute),
            "The token dictionary must remain data-only so compiled WPF can load it.");
    }

    [TestMethod]
    public void SharedFoundation_UsesEventFreePrimitivesInsteadOfTheLegacyWindowDictionary()
    {
        XDocument foundation = LoadXaml("lib/GUI/Resources/KLCodeFoundation.xaml");
        string[] mergedSources = foundation
            .Descendants(Presentation + "ResourceDictionary")
            .Attributes("Source")
            .Select(attribute => attribute.Value)
            .ToArray();

        CollectionAssert.AreEqual(new[] { "KLCodeTokens.xaml", "klIcons.xaml" }, mergedSources);
        CollectionAssert.DoesNotContain(mergedSources, "WPF_styles.xaml");
        foreach (string file in new[] { "KLCodeTokens.xaml", "KLCodeFoundation.xaml", "KLCodeComponents.xaml" })
        {
            XDocument dictionary = LoadXaml("lib/GUI/Resources/" + file);
            Assert.IsFalse(dictionary.Descendants().Attributes().Any(IsEventAttribute), file);
            Assert.AreEqual(0, dictionary.Descendants(Presentation + "EventSetter").Count(), file);
        }
    }

    [TestMethod]
    public void ChromeData_HoldsBothFooterDestinationsAndTheCloseLabel()
    {
        XDocument chrome = LoadXaml("lib/GUI/Resources/KLCodeTokens.xaml");
        XNamespace sys = "clr-namespace:System;assembly=System";
        Dictionary<string, string> entries = chrome.Root!.Elements()
            .ToDictionary(e => (string)e.Attribute(Xaml + "Key")!, e => e.Value.Trim());
        Assert.AreEqual("https", new Uri(entries["klcPrototypeUri"]).Scheme);
        Assert.AreEqual("https", new Uri(entries["klcOutreachUri"]).Scheme);
        Assert.AreNotEqual(entries["klcPrototypeUri"], entries["klcOutreachUri"]);
        Assert.AreEqual("Close", entries["CloseLabel"]);
        // 2026-10-31: only Close is still a DynamicResource label; the footer captions are literal in the shell.
        CollectionAssert.DoesNotContain(entries.Keys.ToArray(), "PrototypeLabel");
        CollectionAssert.DoesNotContain(entries.Keys.ToArray(), "OutreachLabel");
        Assert.AreEqual(2, chrome.Root.Elements(sys + "Uri").Count());
        XDocument foundation = LoadXaml("lib/GUI/Resources/KLCodeFoundation.xaml");
        string shell = foundation.ToString();
        StringAssert.Contains(shell, "{DynamicResource CloseLabel}");
        StringAssert.Contains(shell, "{StaticResource klcPrototypeUri}");
        StringAssert.Contains(shell, "{StaticResource klcOutreachUri}");
        Assert.IsFalse(shell.Contains("PrototypeLabel") || shell.Contains("OutreachLabel"), "footer captions are literal Runs");
        Dictionary<string, string?> captions = foundation.Descendants(Presentation + "Hyperlink")
            .Where(link => ((string?)link.Attribute(Xaml + "Name"))?.StartsWith("klcFooter_", StringComparison.Ordinal) == true)
            .ToDictionary(link => (string)link.Attribute(Xaml + "Name")!, link => (string?)link.Element(Presentation + "Run")?.Attribute("Text"));
        Assert.AreEqual("Prototype", captions["klcFooter_prototype"]);
        Assert.AreEqual("Outreach", captions["klcFooter_outreach"]);
    }

    [TestMethod]
    public void CompiledAdapter_UsesCanonicalResources()
    {
        XDocument controls = LoadXaml("src/KLCode.Wpf/Resources/KLCodeControls.xaml");

        AssertNoColorLiterals(controls, "compiled control resources");
    }

    [TestMethod]
    public void SharedDictionaries_ReferenceBrushesInsteadOfColorLiterals()
    {
        // Only the token dictionary may spell a colour; the style dictionaries name a brush.
        foreach (string file in new[] { "KLCodeFoundation.xaml", "KLCodeComponents.xaml" })
        {
            AssertNoColorLiterals(LoadXaml("lib/GUI/Resources/" + file), file);
        }
    }

    [TestMethod]
    public void CompiledAdapter_AliasesSharedControlsAndLinksTheCanonicalSourceFiles()
    {
        XDocument controls = LoadXaml("src/KLCode.Wpf/Resources/KLCodeControls.xaml");
        HashSet<string> styleKeys = controls
            .Descendants(Presentation + "Style")
            .Select(element => (string?)element.Attribute(Xaml + "Key"))
            .Where(key => key is not null)
            .Select(key => key!)
            .ToHashSet(StringComparer.Ordinal);
        CollectionAssert.IsSubsetOf(RequiredCompiledStyleKeys, styleKeys.ToArray());

        string[] mergedSources = controls
            .Descendants(Presentation + "ResourceDictionary")
            .Attributes("Source")
            .Select(attribute => attribute.Value)
            .ToArray();
        CollectionAssert.Contains(mergedSources, "../GUI/Resources/KLCodeComponents.xaml");
        CollectionAssert.DoesNotContain(mergedSources, "KLCodeCompiledTokens.xaml");
        Assert.AreEqual(0, controls.Descendants(Presentation + "ControlTemplate").Count(),
            "Compiled aliases must not fork shared control templates.");

        XDocument project = XDocument.Load(Path.Combine(FindRepositoryRoot(), "src/KLCode.Wpf/KLCode.Wpf.csproj"));
        foreach (string file in new[] { "KLCodeTokens.xaml", "KLCodeFoundation.xaml", "KLCodeComponents.xaml" })
        {
            XElement? page = project.Descendants("Page")
                .FirstOrDefault(element => (string?)element.Attribute("Include") == "../../lib/GUI/Resources/" + file);
            Assert.IsNotNull(page, "The compiled adapter must link the canonical " + file);
            Assert.AreEqual("GUI/Resources/" + file, (string?)page.Attribute("Link"));
        }
        Assert.IsTrue(project.Descendants("Page").Any(element =>
            (string?)element.Attribute("Link") == "GUI/Resources/klIcons.xaml"));
        Assert.IsFalse(project.Descendants("Page").Any(element =>
            ((string?)element.Attribute("Link") ?? string.Empty).StartsWith("_logos/")),
            "The KLCode logo geometry is generated into klIcons.xaml.");
    }

    [TestMethod]
    public void ApprovedHandoffWindows_UseExactDimensionsAndRequiredChrome()
    {
        AssertWindowContract(
            "src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml",
            "1180", "740",
            "SearchBox", "Results", "GridResults", "Thumbnail", "BatchLoadButton", "EmptyState");
        AssertWindowContract(
            "src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/StartupSourcePickerWindow.xaml",
            "560", "470",
            "ChecklistStatus", "SettingsStatus");
        AssertWindowContract(
            "src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/StartupImportReviewWindow.xaml",
            "860", "640");
        AssertWindowContract(
            "src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/BlockingIssuesWindow.xaml",
            "560", "520");
        AssertWindowContract(
            "src/KLCode.Wpf/Views/KlaAlertWindow.xaml",
            "440", "300",
            "AlertIconBorder", "AlertHeading", "AlertMessage");
    }

    [TestMethod]
    public void RevitConsumers_ReferenceTheAdapter()
    {
        AssertProjectReferencesAdapter(
            "src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/" +
            "KLCode.FamilyStudio.Revit.csproj");
        AssertProjectReferencesAdapter(
            "src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Revit/" +
            "KLA.ModelStartupImporter.Revit.csproj");
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
        CollectionAssert.Contains(mergedSources, "../GUI/Resources/KLCodeComponents.xaml");

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

    internal static string RepositoryRoot() => FindRepositoryRoot();

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

    private static void AssertWindowContract(
        string relativePath,
        string expectedWidth,
        string expectedHeight,
        params string[] requiredNames)
    {
        XDocument window = LoadXaml(relativePath);
        Assert.AreEqual(expectedWidth, (string?)window.Root?.Attribute("Width"), relativePath + " width");
        Assert.AreEqual(expectedHeight, (string?)window.Root?.Attribute("Height"), relativePath + " height");
        CollectionAssert.Contains(new[] { "{StaticResource KlaWindowStyle}", "{StaticResource klcFdnWindow}" },
            (string?)window.Root?.Attribute("Style"));

        HashSet<string> names = window.Descendants()
            .Select(element => (string?)element.Attribute(Xaml + "Name"))
            .Where(name => name is not null)
            .Select(name => name!)
            .ToHashSet(StringComparer.Ordinal);
        CollectionAssert.IsSubsetOf(requiredNames, names.ToArray(), relativePath);

        string source = window.ToString(SaveOptions.DisableFormatting);
        CollectionAssert.IsSubsetOf(new[] { "window_shell", "window_body" }, names.ToArray(), relativePath);
        StringAssert.Contains(source, "klcWindowShell", relativePath);
        Assert.IsFalse(source.Contains("OnHeaderMouseLeftButtonDown", StringComparison.Ordinal));
        Assert.IsFalse(source.Contains("VersionLabel", StringComparison.Ordinal));
    }
}
