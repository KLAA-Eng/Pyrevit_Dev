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
        List<Autodesk.Revit.DB.FamilyParameter> familyParameters = new List<Autodesk.Revit.DB.FamilyParameter>();
        foreach (Autodesk.Revit.DB.FamilyParameter parameter in document.FamilyManager.Parameters)
        {
            familyParameters.Add(parameter);
        }

        List<CatalogFamilyParameter> instanceParameters = new List<CatalogFamilyParameter>();
        foreach (Autodesk.Revit.DB.FamilyParameter parameter in familyParameters)
        {
            if (parameter.IsInstance)
            {
                instanceParameters.Add(new CatalogFamilyParameter(
                    parameter.Definition.Name,
                    null,
                    parameter.StorageType.ToString(),
                    false));
            }
        }

        List<FamilyTypeMetadata> types = new List<FamilyTypeMetadata>();
        List<string> typeNames = new List<string>();
        foreach (FamilyType familyType in document.FamilyManager.Types)
        {
            typeNames.Add(familyType.Name);
            List<CatalogFamilyParameter> typeParameters = new List<CatalogFamilyParameter>();
            foreach (Autodesk.Revit.DB.FamilyParameter parameter in familyParameters)
            {
                if (!parameter.IsInstance)
                {
                    typeParameters.Add(new CatalogFamilyParameter(
                        parameter.Definition.Name,
                        ReadValue(familyType, parameter),
                        parameter.StorageType.ToString(),
                        true));
                }
            }

            types.Add(new FamilyTypeMetadata(familyType.Name, typeParameters.AsReadOnly()));
        }

        string? category = document.OwnerFamily?.FamilyCategory?.Name;
        return new FamilyMetadata(
            filePath,
            Path.GetFileNameWithoutExtension(filePath),
            category,
            _application.VersionNumber,
            typeNames.AsReadOnly(),
            instanceParameters.AsReadOnly(),
            Array.Empty<string>(),
            "Draft",
            null,
            types.AsReadOnly());
    }

    private static string? ReadValue(FamilyType familyType, Autodesk.Revit.DB.FamilyParameter parameter)
    {
        try
        {
            string? valueWithUnits = familyType.AsValueString(parameter);
            if (!string.IsNullOrWhiteSpace(valueWithUnits))
            {
                return valueWithUnits;
            }

            if (parameter.StorageType == StorageType.String)
            {
                return familyType.AsString(parameter);
            }

            if (parameter.StorageType == StorageType.Integer)
            {
                int? value = familyType.AsInteger(parameter);
                return value.HasValue ? value.Value.ToString() : null;
            }

            if (parameter.StorageType == StorageType.ElementId)
            {
                ElementId value = familyType.AsElementId(parameter);
                return value is null || value == ElementId.InvalidElementId ? null : value.Value.ToString();
            }

            double? doubleValue = familyType.AsDouble(parameter);
            return doubleValue.HasValue ? doubleValue.Value.ToString("G") : null;
        }
        catch (Exception)
        {
            return null;
        }
    }
}
