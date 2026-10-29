using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace KLCode.Wpf.Source.Tests;

[TestClass]
public sealed class WindowChromeMetadataTests
{
    [TestMethod]
    public void UnknownCallerVersion_IsOmittedAndNeverInferredFromATitle()
    {
        WindowChromeMetadata metadata = new WindowChromeMetadata("  Sample Tool v2.0  ");
        Assert.AreEqual("Sample Tool v2.0", metadata.Title);
        Assert.AreEqual(string.Empty, metadata.VersionText);
        Assert.AreEqual(string.Empty, new WindowChromeMetadata(null, "not available").VersionText);
    }

    [TestMethod]
    public void ExplicitCallerVersions_FollowThePythonAdapterFormattingContract()
    {
        Assert.AreEqual("v0.0", new WindowChromeMetadata("Tool", "v0.0").VersionText);
        Assert.AreEqual("v1.2", new WindowChromeMetadata("Tool", "Version: 1.2").VersionText);
        Assert.AreEqual("v1.2.Source", new WindowChromeMetadata("Tool", "version= V1.2.Source").VersionText);
        Assert.AreEqual(string.Empty, new WindowChromeMetadata("Tool", "Version: _").VersionText);
    }

    [TestMethod]
    public void FooterDestinations_AreAbsoluteHttpsUris()
    {
        WindowChromeMetadata metadata = new WindowChromeMetadata("Tool");
        Assert.AreEqual("https", metadata.PrototypeUri.Scheme);
        Assert.AreEqual("https", metadata.OutreachUri.Scheme);
        Assert.AreNotEqual(metadata.PrototypeUri, metadata.OutreachUri);
    }
}
