using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.DB;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;
using CatalogFamilyParameter = KLCode.FamilyStudio.Core.Models.FamilyParameter;

namespace KLCode.FamilyStudio.Revit.Services;

internal sealed class RevitFamilyMetadataExtractor : IMetadataExtractor
{
    private readonly Application _application;

    public RevitFamilyMetadataExtractor(Application application)
    {
        _application = application ?? throw new ArgumentNullException(nameof(application));
    }

    public Task<FamilyMetadata> ExtractAsync(string filePath, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException("The family file is not available.", filePath);
        }

        Document document = _application.OpenDocumentFile(filePath);
        try
        {
            if (!document.IsFamilyDocument)
            {
                throw new InvalidDataException("The selected file is not a Revit family document.");
            }

            return Task.FromResult(ReadMetadata(document, filePath));
        }
        finally
        {
            document.Close(false);
        }
    }

    private FamilyMetadata ReadMetadata(Document document, string filePath)
    {
        List<string> typeNames = new List<string>();
        foreach (FamilyType familyType in document.FamilyManager.Types)
        {
            typeNames.Add(familyType.Name);
        }

        List<CatalogFamilyParameter> parameters = new List<CatalogFamilyParameter>();
        foreach (Autodesk.Revit.DB.FamilyParameter parameter in document.FamilyManager.Parameters)
        {
            parameters.Add(new CatalogFamilyParameter(
                parameter.Definition.Name,
                null,
                parameter.StorageType.ToString(),
                !parameter.IsInstance));
        }

        string? category = document.OwnerFamily?.FamilyCategory?.Name;
        return new FamilyMetadata(
            filePath,
            Path.GetFileNameWithoutExtension(filePath),
            category,
            _application.VersionNumber,
            typeNames.AsReadOnly(),
            parameters.AsReadOnly(),
            Array.Empty<string>(),
            "Draft",
            null);
    }
}
