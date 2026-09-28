using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace KLCode.Wpf.Source.Tests;

[TestClass]
public sealed class SupportedLocaleCatalogTests
{
    [TestMethod]
    public void All_ExposesTheApprovedEightLocaleInventory()
    {
        CollectionAssert.AreEqual(
            new[]
            {
                "en_us",
                "ko",
                "fr_fr",
                "ru",
                "chinese_s",
                "es_es",
                "de_de",
                "pt_br",
            },
            SupportedLocaleCatalog.All.ToArray());
    }

    [TestMethod]
    public void SelectAvailableLocale_NormalizesAndSelectsAnAvailableTranslation()
    {
        string selected = SupportedLocaleCatalog.SelectAvailableLocale(
            "FR-FR",
            new[] { "en_us", "fr_fr" });

        Assert.AreEqual("fr_fr", selected);
    }

    [TestMethod]
    public void SelectAvailableLocale_MapsFrameworkCultureNamesToPyRevitLocales()
    {
        string[] available = SupportedLocaleCatalog.All.ToArray();

        Assert.AreEqual(
            "ko",
            SupportedLocaleCatalog.SelectAvailableLocale("ko-KR", available));
        Assert.AreEqual(
            "ru",
            SupportedLocaleCatalog.SelectAvailableLocale("ru-RU", available));
        Assert.AreEqual(
            "chinese_s",
            SupportedLocaleCatalog.SelectAvailableLocale("zh-CN", available));
    }

    [TestMethod]
    public void SelectAvailableLocale_FallsBackForUnknownOrUnavailableLocales()
    {
        Assert.AreEqual(
            "en_us",
            SupportedLocaleCatalog.SelectAvailableLocale("ja_jp", new[] { "en_us" }));
        Assert.AreEqual(
            "en_us",
            SupportedLocaleCatalog.SelectAvailableLocale("de_de", new[] { "en_us" }));
    }

    [TestMethod]
    public void SelectAvailableLocale_RejectsAnInventoryWithoutEnglish()
    {
        Assert.ThrowsExactly<InvalidOperationException>(
            () => SupportedLocaleCatalog.SelectAvailableLocale("fr_fr", new[] { "fr_fr" }));
    }

    [TestMethod]
    public void SelectAvailableLocale_RejectsMalformedInventoryEntries()
    {
        Assert.ThrowsExactly<ArgumentException>(
            () => SupportedLocaleCatalog.SelectAvailableLocale(
                "en_us",
                new[] { "en_us", null! }));
    }
}
