using System;
using System.Collections.Generic;
using System.IO;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.DB;

namespace KLCode.FamilyStudio.Revit.Services;

internal sealed class RevitFamilyDocumentSession
{
    private readonly Application _application;
    private readonly IDictionary<string, Document> _documents =
        new Dictionary<string, Document>(StringComparer.OrdinalIgnoreCase);

    internal RevitFamilyDocumentSession(Application application)
    {
        _application = application ?? throw new ArgumentNullException(nameof(application));
    }

    internal Document Open(string filePath)
    {
        if (string.IsNullOrWhiteSpace(filePath)) throw new ArgumentException("A family path is required.", nameof(filePath));
        if (!File.Exists(filePath)) throw new FileNotFoundException("The family file is not available.", filePath);

        if (_documents.TryGetValue(filePath, out Document document)) return document;

        document = _application.OpenDocumentFile(filePath);
        _documents.Add(filePath, document);
        return document;
    }

    internal void Close(string filePath)
    {
        if (!_documents.TryGetValue(filePath, out Document document)) return;

        _documents.Remove(filePath);
        document.Close(false);
    }
}
