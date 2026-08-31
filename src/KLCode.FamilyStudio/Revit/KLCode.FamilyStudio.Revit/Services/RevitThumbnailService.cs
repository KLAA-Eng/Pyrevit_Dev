using System;
using System.Collections.Generic;
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
    // Revit exports this exact 4:3 canvas.  The Family Studio detail pane uses
    // the same dimensions, so the cached PNG is never resized or cropped later.
    private const int PreviewWidthPixels = 400;
    private const int PreviewHeightPixels = 300;
    private const double PreviewAspectRatio = (double)PreviewWidthPixels / PreviewHeightPixels;
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
        Document document = _application.OpenDocumentFile(metadata.SourcePath);
        try
        {
            cancellationToken.ThrowIfCancellationRequested();
            List<FamilyPreview> typedPreviews = CreateTypePreviews(document, metadata, directory, cancellationToken);
            if (typedPreviews.Count > 0)
            {
                return Task.FromResult(ThumbnailResult.FromPreviews(typedPreviews));
            }

            string outputPath = Path.Combine(directory, CreateCacheName(metadata.SourcePath, null));
            MigrateLegacyCacheEntry(directory, metadata.SourcePath, outputPath);
            ExportFamilyView(document, directory, outputPath);
            return Task.FromResult(ThumbnailResult.Created(outputPath));
        }
        finally
        {
            document.Close(false);
        }
    }

    private static List<FamilyPreview> CreateTypePreviews(
        Document document,
        FamilyMetadata metadata,
        string directory,
        CancellationToken cancellationToken)
    {
        List<FamilyType> familyTypes = document.FamilyManager.Types
            .Cast<FamilyType>()
            .ToList();
        List<FamilyPreview> previews = new List<FamilyPreview>();
        int typeCount = Math.Min(familyTypes.Count, metadata.Types.Count);
        for (int index = 0; index < typeCount; index++)
        {
            cancellationToken.ThrowIfCancellationRequested();
            FamilyType familyType = familyTypes[index];
            string typeName = metadata.Types[index].Name;

            try
            {
                ActivateFamilyType(document, familyType);
                string outputPath = Path.Combine(directory, CreateCacheName(metadata.SourcePath, typeName));
                ExportFamilyView(document, directory, outputPath);
                previews.Add(new FamilyPreview(typeName, outputPath));
            }
            catch
            {
                // Try the next type; the family-level view fallback remains available if none render.
            }
        }

        return previews;
    }

    private static void ActivateFamilyType(Document document, FamilyType familyType)
    {
        // This is an in-memory, disposable family document.  Activating the
        // type and regenerating it ensures the exported geometry represents
        // this exact type rather than Revit's generic symbol preview.
        using Transaction transaction = new Transaction(document, "Activate Family Studio Preview Type");
        transaction.Start();
        document.FamilyManager.CurrentType = familyType;
        document.Regenerate();
        transaction.Commit();
    }

    private static void ExportFamilyView(Document document, string directory, string outputPath)
    {
        View? view = new FilteredElementCollector(document)
            .OfClass(typeof(View3D))
            .Cast<View3D>()
            .FirstOrDefault(candidate => !candidate.IsTemplate && candidate.CanBePrinted);
        view ??= new FilteredElementCollector(document)
            .OfClass(typeof(View))
            .Cast<View>()
            .FirstOrDefault(candidate => !candidate.IsTemplate && candidate.CanBePrinted);
        if (view is null)
        {
            throw new InvalidOperationException(
                "Revit did not provide a family-type preview or a printable family view to export.");
        }

        // The default family 3D view already carries its own camera/framing.
        // Respect that framing: bounding-box crops make some 3D families look
        // artificially distant.  Two-dimensional family views still receive
        // the tight 4:3 content crop below.
        if (!(view is View3D))
        {
            FitViewToContent(document, view);
        }

        string exportPrefix = Path.Combine(
            directory,
            Path.GetFileNameWithoutExtension(outputPath));
        using ImageExportOptions options = new ImageExportOptions
        {
            ExportRange = ExportRange.SetOfViews,
            FilePath = exportPrefix,
            FitDirection = FitDirectionType.Horizontal,
            HLRandWFViewsFileType = ImageFileType.PNG,
            ShadowViewsFileType = ImageFileType.PNG,
            PixelSize = PreviewWidthPixels,
            ShouldCreateWebSite = false,
            ZoomType = ZoomFitType.FitToPage,
        };
        options.SetViewsAndSheets(new List<ElementId> { view.Id });
        Dictionary<string, FileSignature> previousImages = SnapshotPreviewCandidates(directory, outputPath);
        try
        {
            document.ExportImage(options);
            string? exportedPath = FindExportedImage(directory, outputPath, previousImages);
            if (string.IsNullOrWhiteSpace(exportedPath) || !File.Exists(exportedPath))
            {
                throw new IOException("Revit did not create the exported family preview image.");
            }

            PromotePreview(exportedPath!, outputPath);
            exportedPath = null;
        }
        finally
        {
            foreach (string candidate in Directory.EnumerateFiles(
                directory,
                Path.GetFileNameWithoutExtension(outputPath) + "*.png",
                SearchOption.TopDirectoryOnly))
            {
                if (!string.Equals(candidate, outputPath, StringComparison.OrdinalIgnoreCase))
                {
                    File.Delete(candidate);
                }
            }
        }
    }

    private static void FitViewToContent(Document document, View view)
    {
        try
        {
            BoundingBoxXYZ? cropBox = view.CropBox;
            if (cropBox is null)
            {
                return;
            }

            PreviewBounds? contentBounds = FindPreviewContentBounds(document, view, cropBox.Transform.Inverse);
            if (contentBounds is null)
            {
                return;
            }

            // This transaction affects only the opened, disposable family document.
            // The document is always closed without saving after the image export.
            using Transaction transaction = new Transaction(document, "Fit Family Studio Preview");
            transaction.Start();
            try
            {
                // Keep the object legible at 400 x 300 while leaving a small,
                // deliberate edge buffer.  Cropping happens inside Revit before
                // export; the PNG itself is not post-processed.
                // Deliberately use a near-full-bleed crop.  Revit's image
                // export retains a small fit-to-page canvas of its own, so a
                // conservative source margin makes the family look too small.
                double margin = Math.Max(Math.Max(contentBounds.Width, contentBounds.Height) * 0.005, 0.001);
                double width = contentBounds.Width + (2 * margin);
                double height = contentBounds.Height + (2 * margin);
                if (width / height > PreviewAspectRatio)
                {
                    height = width / PreviewAspectRatio;
                }
                else
                {
                    width = height * PreviewAspectRatio;
                }

                double centerX = (contentBounds.MinX + contentBounds.MaxX) / 2;
                double centerY = (contentBounds.MinY + contentBounds.MaxY) / 2;
                view.CropBoxActive = true;
                view.CropBox = new BoundingBoxXYZ
                {
                    Transform = cropBox.Transform,
                    Min = new XYZ(centerX - (width / 2), centerY - (height / 2), cropBox.Min.Z),
                    Max = new XYZ(centerX + (width / 2), centerY + (height / 2), cropBox.Max.Z),
                };
                try
                {
                    // Some family views do not allow this optional display
                    // setting.  That must not undo the crop that defines the
                    // native 4:3 export area.
                    view.CropBoxVisible = false;
                }
                catch
                {
                    // The crop itself remains valid and will still be applied.
                }

                document.Regenerate();
                transaction.Commit();
            }
            catch
            {
                transaction.RollBack();
            }
        }
        catch
        {
            // A view that cannot be cropped still receives the standard full-view export.
        }
    }

    private static PreviewBounds? FindPreviewContentBounds(Document document, View view, Transform toCropCoordinates)
    {
        PreviewBounds? bounds = null;
        foreach (Element element in new FilteredElementCollector(document, view.Id).WhereElementIsNotElementType())
        {
            if (!IsPreviewContent(element))
            {
                continue;
            }

            BoundingBoxXYZ? elementBounds = element.get_BoundingBox(view);
            if (elementBounds is null)
            {
                continue;
            }

            foreach (XYZ corner in GetCorners(elementBounds))
            {
                XYZ point = toCropCoordinates.OfPoint(corner);
                bounds = bounds is null
                    ? new PreviewBounds(point.X, point.Y)
                    : bounds.Include(point.X, point.Y);
            }
        }

        return bounds;
    }

    private static bool IsPreviewContent(Element element)
    {
        return !(element is View) &&
               !(element is ReferencePlane) &&
               !(element is Level) &&
               !(element is Grid) &&
               !(element is SketchPlane) &&
               !(element is Dimension) &&
               !(element is TextNote);
    }

    private static IEnumerable<XYZ> GetCorners(BoundingBoxXYZ box)
    {
        foreach (double x in new[] { box.Min.X, box.Max.X })
        {
            foreach (double y in new[] { box.Min.Y, box.Max.Y })
            {
                foreach (double z in new[] { box.Min.Z, box.Max.Z })
                {
                    yield return new XYZ(x, y, z);
                }
            }
        }
    }

    private static Dictionary<string, FileSignature> SnapshotPreviewCandidates(string directory, string outputPath)
    {
        string pattern = Path.GetFileNameWithoutExtension(outputPath) + "*.png";
        return Directory.EnumerateFiles(directory, pattern, SearchOption.TopDirectoryOnly)
            .Where(path => !string.Equals(path, outputPath, StringComparison.OrdinalIgnoreCase))
            .ToDictionary(path => path, path => new FileSignature(new FileInfo(path)));
    }

    private static string? FindExportedImage(
        string directory,
        string outputPath,
        IReadOnlyDictionary<string, FileSignature> previousImages)
    {
        string pattern = Path.GetFileNameWithoutExtension(outputPath) + "*.png";
        return Directory.EnumerateFiles(directory, pattern, SearchOption.TopDirectoryOnly)
            .Where(path => !string.Equals(path, outputPath, StringComparison.OrdinalIgnoreCase))
            .Select(path => new { Path = path, Signature = new FileSignature(new FileInfo(path)) })
            .Where(candidate => !previousImages.TryGetValue(candidate.Path, out FileSignature previous) || !candidate.Signature.Equals(previous))
            .OrderByDescending(candidate => candidate.Signature.LastWriteUtc)
            .Select(candidate => candidate.Path)
            .FirstOrDefault();
    }

    private static void PromotePreview(string temporaryPath, string outputPath)
    {
        if (File.Exists(outputPath))
        {
            File.Replace(temporaryPath, outputPath, null);
        }
        else
        {
            File.Move(temporaryPath, outputPath);
        }
    }

    private static string CreateCacheName(string sourcePath, string? typeName)
    {
        string familyName = NormalizeFileNamePart(Path.GetFileNameWithoutExtension(sourcePath), "family");
        string typePart = typeName is null
            ? string.Empty
            : "--" + NormalizeFileNamePart(typeName, "type");
        return familyName + typePart + "--" + CreateHash(sourcePath + "\n" + (typeName ?? string.Empty)).Substring(0, 12) + ".png";
    }

    private static string NormalizeFileNamePart(string value, string fallback)
    {
        string result = value;
        foreach (char invalidCharacter in Path.GetInvalidFileNameChars())
        {
            result = result.Replace(invalidCharacter, '_');
        }

        result = result.Trim().TrimEnd('.');
        if (string.IsNullOrWhiteSpace(result))
        {
            return fallback;
        }

        return result;
    }

    private static void MigrateLegacyCacheEntry(string directory, string sourcePath, string outputPath)
    {
        string legacyPath = Path.Combine(directory, CreateHash(sourcePath) + ".png");
        if (File.Exists(legacyPath) && !File.Exists(outputPath))
        {
            File.Move(legacyPath, outputPath);
        }
    }

    private static string CreateHash(string sourcePath)
    {
        using SHA256 hash = SHA256.Create();
        byte[] bytes = hash.ComputeHash(Encoding.UTF8.GetBytes(sourcePath));
        return BitConverter.ToString(bytes).Replace("-", string.Empty);
    }

    private readonly struct FileSignature : IEquatable<FileSignature>
    {
        internal FileSignature(FileInfo file)
        {
            LastWriteUtc = file.LastWriteTimeUtc;
            Length = file.Length;
        }

        internal DateTime LastWriteUtc { get; }
        private long Length { get; }

        public bool Equals(FileSignature other)
        {
            return LastWriteUtc == other.LastWriteUtc && Length == other.Length;
        }

        public override bool Equals(object? obj)
        {
            return obj is FileSignature other && Equals(other);
        }

        public override int GetHashCode()
        {
            unchecked
            {
                return (LastWriteUtc.GetHashCode() * 397) ^ Length.GetHashCode();
            }
        }
    }

    private sealed class PreviewBounds
    {
        internal PreviewBounds(double x, double y)
        {
            MinX = MaxX = x;
            MinY = MaxY = y;
        }

        internal double MinX { get; }
        internal double MinY { get; }
        internal double MaxX { get; }
        internal double MaxY { get; }
        internal double Width => MaxX - MinX;
        internal double Height => MaxY - MinY;

        internal PreviewBounds Include(double x, double y)
        {
            return new PreviewBounds(
                Math.Min(MinX, x),
                Math.Min(MinY, y),
                Math.Max(MaxX, x),
                Math.Max(MaxY, y));
        }

        private PreviewBounds(double minX, double minY, double maxX, double maxY)
        {
            MinX = minX;
            MinY = minY;
            MaxX = maxX;
            MaxY = maxY;
        }
    }
}
