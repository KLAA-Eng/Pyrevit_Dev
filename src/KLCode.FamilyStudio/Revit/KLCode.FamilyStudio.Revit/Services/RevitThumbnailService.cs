using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Autodesk.Revit.DB;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;

namespace KLCode.FamilyStudio.Revit.Services;

internal sealed class RevitThumbnailService : IThumbnailService
{
    private readonly Autodesk.Revit.ApplicationServices.Application _application;

    internal RevitThumbnailService(Autodesk.Revit.ApplicationServices.Application application)
    {
        _application = application ?? throw new ArgumentNullException(nameof(application));
    }

    public Task<ThumbnailResult> EnsureThumbnailAsync(
        FamilyMetadata metadata,
        string thumbnailDirectory,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (metadata is null)
        {
            throw new ArgumentNullException(nameof(metadata));
        }

        string directory = Path.GetFullPath(thumbnailDirectory ?? throw new ArgumentNullException(nameof(thumbnailDirectory)));
        Directory.CreateDirectory(directory);
        string outputPath = Path.Combine(directory, CreateCacheName(metadata.SourcePath));
        Document document = _application.OpenDocumentFile(metadata.SourcePath);
        try
        {
            cancellationToken.ThrowIfCancellationRequested();
            FamilySymbol? symbol = new FilteredElementCollector(document)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .OrderBy(candidate => candidate.Name, StringComparer.OrdinalIgnoreCase)
                .FirstOrDefault();
            if (symbol is null)
            {
                throw new InvalidOperationException("The family has no type that Revit can render as a preview.");
            }

            using Bitmap bitmap = symbol.GetPreviewImage(new Size(360, 240));
            if (bitmap is null)
            {
                throw new InvalidOperationException("Revit did not return a preview image for this family type.");
            }

            string temporaryPath = outputPath + "." + Guid.NewGuid().ToString("N") + ".tmp";
            try
            {
                bitmap.Save(temporaryPath, ImageFormat.Png);
                if (File.Exists(outputPath))
                {
                    File.Replace(temporaryPath, outputPath, null);
                }
                else
                {
                    File.Move(temporaryPath, outputPath);
                }

                return Task.FromResult(ThumbnailResult.Created(outputPath));
            }
            finally
            {
                if (File.Exists(temporaryPath))
                {
                    File.Delete(temporaryPath);
                }
            }
        }
        finally
        {
            document.Close(false);
        }
    }

    private static string CreateCacheName(string sourcePath)
    {
        using SHA256 hash = SHA256.Create();
        byte[] bytes = hash.ComputeHash(Encoding.UTF8.GetBytes(sourcePath));
        return BitConverter.ToString(bytes).Replace("-", string.Empty) + ".png";
    }
}
