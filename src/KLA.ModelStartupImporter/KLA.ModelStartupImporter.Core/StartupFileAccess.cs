using System;
using System.IO;

namespace KLA.ModelStartupImporter.Core;

internal readonly struct StartupFileMetadata : IEquatable<StartupFileMetadata>
{
    internal StartupFileMetadata(long length, DateTime modifiedUtc)
    {
        Length = length;
        ModifiedUtc = modifiedUtc;
    }

    internal long Length { get; }

    internal DateTime ModifiedUtc { get; }

    public bool Equals(StartupFileMetadata other)
    {
        return Length == other.Length && ModifiedUtc == other.ModifiedUtc;
    }

    public override bool Equals(object? value)
    {
        return value is StartupFileMetadata other && Equals(other);
    }

    public override int GetHashCode()
    {
        unchecked
        {
            return (Length.GetHashCode() * 397) ^ ModifiedUtc.GetHashCode();
        }
    }
}

internal interface IStartupFileAccess
{
    bool Exists(string path);

    StartupFileMetadata GetMetadata(string path);

    byte[] ReadAllBytes(string path);
}

internal sealed class PhysicalStartupFileAccess : IStartupFileAccess
{
    public bool Exists(string path)
    {
        return File.Exists(path);
    }

    public StartupFileMetadata GetMetadata(string path)
    {
        var fileInfo = new FileInfo(path);
        fileInfo.Refresh();
        return new StartupFileMetadata(fileInfo.Length, fileInfo.LastWriteTimeUtc);
    }

    public byte[] ReadAllBytes(string path)
    {
        return File.ReadAllBytes(path);
    }
}
