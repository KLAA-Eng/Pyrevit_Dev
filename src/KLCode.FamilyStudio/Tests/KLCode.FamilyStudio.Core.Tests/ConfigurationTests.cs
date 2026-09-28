using System;
using System.IO;
using KLCode.FamilyStudio.Core.Configuration;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace KLCode.FamilyStudio.Core.Tests;

[TestClass]
public sealed class ConfigurationTests
{
    [TestMethod]
    public void Load_NormalizesValidPathsAndKeepsEnabledRoot()
    {
        using TempDirectory temp = new TempDirectory();
        string root = temp.CreateDirectory("library");
        string configPath = temp.WriteFile(
            "config.json",
            "{\"libraryRoots\":[{\"path\":\"library\",\"enabled\":true}]," +
            "\"databasePath\":\"cache/index.sqlite\",\"thumbnailDirectory\":\"cache/thumbs\"}");

        LibraryConfiguration config = new JsonLibraryConfigurationProvider().Load(configPath);

        Assert.AreEqual(Path.GetFullPath(root), config.LibraryRoots[0].Path);
        Assert.AreEqual(Path.GetFullPath(Path.Combine(temp.Path, "cache/index.sqlite")), config.DatabasePath);
        Assert.IsTrue(config.LibraryRoots[0].IsEnabled);
    }

    [TestMethod]
    public void Load_RejectsConfigurationWithoutEnabledRoots()
    {
        using TempDirectory temp = new TempDirectory();
        string configPath = temp.WriteFile(
            "config.json",
            "{\"libraryRoots\":[{\"path\":\"library\",\"enabled\":false}]," +
            "\"databasePath\":\"cache/index.sqlite\",\"thumbnailDirectory\":\"cache/thumbs\"}");

        Assert.ThrowsExactly<ConfigurationException>(
            () => new JsonLibraryConfigurationProvider().Load(configPath));
    }
}
