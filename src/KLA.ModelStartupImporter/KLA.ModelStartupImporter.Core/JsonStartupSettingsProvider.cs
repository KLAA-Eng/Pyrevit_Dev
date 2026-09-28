using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;

namespace KLA.ModelStartupImporter.Core;

public sealed class JsonStartupSettingsProvider : IStartupSettingsProvider
{
    private const long MaximumSettingsBytes = 1024 * 1024;
    private const long MaximumCatalogBytes = 5 * 1024 * 1024;

    public StartupImportSettings Load(string settingsPath)
    {
        string fullSettingsPath = ValidateFile(settingsPath, MaximumSettingsBytes, "The Startup Importer settings file");
        string settingsDirectory = Path.GetDirectoryName(fullSettingsPath)!;
        SettingsDocument settings = Read<SettingsDocument>(fullSettingsPath, "The Startup Importer settings file");
        string seedModelPath = ResolveExistingPath(settings.SeedModelPath, settingsDirectory, "seedModelPath", ".rvt");
        string catalogPath = ResolveExistingPath(settings.CatalogPath, settingsDirectory, "catalogPath", ".json");
        CatalogDocument catalogDocument = Read<CatalogDocument>(
            ValidateFile(catalogPath, MaximumCatalogBytes, "The Startup Importer catalog file"),
            "The Startup Importer catalog file");
        string catalogVersion = catalogDocument.Version ?? string.Empty;
        if (string.IsNullOrWhiteSpace(catalogVersion))
        {
            throw new StartupSettingsException("The catalog must declare a non-empty version.");
        }

        if (catalogDocument.Items is null || catalogDocument.Items.Count == 0)
        {
            throw new StartupSettingsException("The catalog must declare at least one item.");
        }

        return new StartupImportSettings(
            seedModelPath,
            catalogVersion,
            new ContentCatalog(catalogDocument.Items.Select(CreateCatalogItem)));
    }

    private static T Read<T>(string path, string label)
        where T : class
    {
        try
        {
            using FileStream stream = File.OpenRead(path);
            DataContractJsonSerializer serializer = new DataContractJsonSerializer(typeof(T));
            T? document = serializer.ReadObject(stream) as T;
            return document ?? throw new StartupSettingsException(label + " is empty.");
        }
        catch (StartupSettingsException)
        {
            throw;
        }
        catch (Exception exception) when (exception is IOException || exception is SerializationException)
        {
            throw new StartupSettingsException(label + " could not be read.", exception);
        }
    }

    private static string ValidateFile(string path, long maximumLength, string label)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            throw new StartupSettingsException(label + " path is required.");
        }

        FileInfo file = new FileInfo(Path.GetFullPath(path));
        if (!file.Exists)
        {
            throw new StartupSettingsException(label + " does not exist.");
        }

        if (file.Length > maximumLength)
        {
            throw new StartupSettingsException(label + " exceeds the allowed size.");
        }

        return file.FullName;
    }

    private static string ResolveExistingPath(string? value, string baseDirectory, string propertyName, string extension)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new StartupSettingsException(propertyName + " must be a non-empty path.");
        }

        string requiredValue = value!;
        string path = Path.IsPathRooted(requiredValue) ? requiredValue : Path.Combine(baseDirectory, requiredValue);
        string fullPath = Path.GetFullPath(path);
        if (!string.Equals(Path.GetExtension(fullPath), extension, StringComparison.OrdinalIgnoreCase))
        {
            throw new StartupSettingsException(propertyName + " must reference a " + extension + " file.");
        }

        if (!File.Exists(fullPath))
        {
            throw new StartupSettingsException(propertyName + " does not exist.");
        }

        return fullPath;
    }

    private static CatalogItem CreateCatalogItem(CatalogItemDocument document)
    {
        if (document is null)
        {
            throw new StartupSettingsException("The catalog contains an empty item.");
        }

        return new CatalogItem(
            Required(document.ItemId, "itemId"),
            Required(document.SourceViewName, "sourceViewName"),
            Required(document.TargetName, "targetName"),
            ParseCategory(document.ContentType),
            document.RequiredTextTypeNames is null ? Array.Empty<string>() : document.RequiredTextTypeNames,
            document.RequiredLineStyleNames is null ? Array.Empty<string>() : document.RequiredLineStyleNames);
    }

    private static string Required(string? value, string propertyName)
    {
        return string.IsNullOrWhiteSpace(value)
            ? throw new StartupSettingsException("Catalog " + propertyName + " is required.")
            : value!.Trim();
    }

    private static StartupItemCategory ParseCategory(string? value)
    {
        string requiredValue = Required(value, "contentType");
        string normalized = requiredValue.Replace(" ", string.Empty).Replace("_", string.Empty);
        return string.Equals(normalized, "detail", StringComparison.OrdinalIgnoreCase) ? StartupItemCategory.Detail :
               string.Equals(normalized, "generalnote", StringComparison.OrdinalIgnoreCase) ? StartupItemCategory.GeneralNote :
               string.Equals(normalized, "schedule", StringComparison.OrdinalIgnoreCase) ? StartupItemCategory.Schedule :
               string.Equals(normalized, "other", StringComparison.OrdinalIgnoreCase) ? StartupItemCategory.Other :
               throw new StartupSettingsException("Catalog contentType is not supported: " + requiredValue + ".");
    }

    [DataContract]
    private sealed class SettingsDocument
    {
        [DataMember(Name = "seedModelPath")]
        public string? SeedModelPath { get; set; }

        [DataMember(Name = "catalogPath")]
        public string? CatalogPath { get; set; }
    }

    [DataContract]
    private sealed class CatalogDocument
    {
        [DataMember(Name = "version")]
        public string? Version { get; set; }

        [DataMember(Name = "items")]
        public List<CatalogItemDocument>? Items { get; set; }
    }

    [DataContract]
    private sealed class CatalogItemDocument
    {
        [DataMember(Name = "itemId")]
        public string? ItemId { get; set; }

        [DataMember(Name = "sourceViewName")]
        public string? SourceViewName { get; set; }

        [DataMember(Name = "targetName")]
        public string? TargetName { get; set; }

        [DataMember(Name = "contentType")]
        public string? ContentType { get; set; }

        [DataMember(Name = "requiredTextTypeNames")]
        public List<string>? RequiredTextTypeNames { get; set; }

        [DataMember(Name = "requiredLineStyleNames")]
        public List<string>? RequiredLineStyleNames { get; set; }
    }
}

public sealed class StartupSettingsException : Exception
{
    public StartupSettingsException(string message)
        : base(message)
    {
    }

    public StartupSettingsException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}
