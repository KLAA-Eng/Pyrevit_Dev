using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using KLCode.FamilyStudio.Core.Configuration;

namespace KLCode.FamilyStudio.Core.Indexing;

public sealed class FileSystemLibraryScanner : ILibraryScanner
{
    public LibraryScanResult Scan(LibraryConfiguration configuration)
    {
        if (configuration is null)
        {
            throw new ArgumentNullException(nameof(configuration));
        }

        List<LibraryFileCandidate> files = new List<LibraryFileCandidate>();
        List<LibraryScanIssue> issues = new List<LibraryScanIssue>();
        foreach (LibraryRoot root in configuration.LibraryRoots.Where(item => item.IsEnabled))
        {
            ScanRoot(root.Path, files, issues);
        }

        LibraryFileCandidate[] orderedFiles = files
            .GroupBy(file => file.FilePath, StringComparer.OrdinalIgnoreCase)
            .Select(group => group.First())
            .OrderBy(file => file.FilePath, StringComparer.OrdinalIgnoreCase)
            .ToArray();
        return new LibraryScanResult(Array.AsReadOnly(orderedFiles), issues.AsReadOnly());
    }

    private static void ScanRoot(
        string rootPath,
        ICollection<LibraryFileCandidate> files,
        ICollection<LibraryScanIssue> issues)
    {
        if (string.IsNullOrWhiteSpace(rootPath))
        {
            issues.Add(new LibraryScanIssue(rootPath ?? string.Empty, "Library root is empty."));
            return;
        }

        rootPath = Path.GetFullPath(rootPath);
        if (!Directory.Exists(rootPath))
        {
            issues.Add(new LibraryScanIssue(rootPath, "Library root does not exist."));
            return;
        }

        if (IsReparsePoint(rootPath))
        {
            issues.Add(new LibraryScanIssue(rootPath, "Symbolic-link or reparse-point roots are not indexed."));
            return;
        }

        Stack<string> pending = new Stack<string>();
        pending.Push(rootPath);
        while (pending.Count > 0)
        {
            ScanDirectory(pending.Pop(), pending, files, issues);
        }
    }

    private static void ScanDirectory(
        string directory,
        Stack<string> pending,
        ICollection<LibraryFileCandidate> files,
        ICollection<LibraryScanIssue> issues)
    {
        try
        {
            AddFiles(directory, files, issues);
            foreach (string child in Directory.EnumerateDirectories(directory).OrderBy(path => path, StringComparer.OrdinalIgnoreCase))
            {
                if (IsReparsePoint(child))
                {
                    issues.Add(new LibraryScanIssue(child, "Symbolic-link or reparse-point directories are not indexed."));
                    continue;
                }

                pending.Push(child);
            }
        }
        catch (Exception exception) when (exception is IOException || exception is UnauthorizedAccessException)
        {
            issues.Add(new LibraryScanIssue(directory, "Directory could not be scanned: " + exception.Message));
        }
    }

    private static void AddFiles(
        string directory,
        ICollection<LibraryFileCandidate> files,
        ICollection<LibraryScanIssue> issues)
    {
        foreach (string path in Directory.EnumerateFiles(directory))
        {
            if (!string.Equals(Path.GetExtension(path), ".rfa", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            if (IsReparsePoint(path))
            {
                issues.Add(new LibraryScanIssue(path, "Symbolic-link or reparse-point files are not indexed."));
                continue;
            }

            FileInfo info = new FileInfo(path);
            files.Add(new LibraryFileCandidate(info.FullName, info.Length, info.LastWriteTimeUtc));
        }
    }

    private static bool IsReparsePoint(string path)
    {
        return (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0;
    }
}
