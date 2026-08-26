using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;
using KLCode.FamilyStudio.Core.Repositories;
using KLCode.FamilyStudio.Core.Search;
using KLCode.FamilyStudio.Database.Migrations;
using Microsoft.Data.Sqlite;

namespace KLCode.FamilyStudio.Database.Repositories;

public sealed class SqliteFamilyRepository : IFamilyRepository, IDisposable
{
    private const int MaximumSearchLimit = 200;
    private readonly string _connectionString;

    public SqliteFamilyRepository(string databasePath)
    {
        if (string.IsNullOrWhiteSpace(databasePath))
        {
            throw new ArgumentException("A database path is required.", nameof(databasePath));
        }

        string fullPath = Path.GetFullPath(databasePath);
        Directory.CreateDirectory(Path.GetDirectoryName(fullPath)!);
        _connectionString = new SqliteConnectionStringBuilder
        {
            DataSource = fullPath,
            Mode = SqliteOpenMode.ReadWriteCreate
        }.ToString();
        using SqliteConnection connection = OpenConnection();
        SqliteMigrationRunner.Apply(connection);
    }

    public IndexedFileState? GetIndexedFile(string filePath)
    {
        using SqliteConnection connection = OpenConnection();
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = @"SELECT file_path, file_size, modified_utc, file_hash
FROM families WHERE file_path = $path AND is_deleted = 0;";
        command.Parameters.AddWithValue("$path", ValidateFilePath(filePath));
        using SqliteDataReader reader = command.ExecuteReader();
        return reader.Read()
            ? new IndexedFileState(reader.GetString(0), reader.GetInt64(1), ParseTimestamp(reader.GetString(2)), GetNullableString(reader, 3))
            : null;
    }

    public void Upsert(
        FamilyMetadata metadata,
        LibraryFileCandidate file,
        ThumbnailResult thumbnail,
        DateTimeOffset indexedUtc)
    {
        ValidateUpsert(metadata, file, thumbnail);
        using SqliteConnection connection = OpenConnection();
        using SqliteTransaction transaction = connection.BeginTransaction();
        long familyId = UpsertFamily(connection, transaction, metadata, file, thumbnail, indexedUtc);
        ReplaceDetails(connection, transaction, familyId, metadata);
        transaction.Commit();
    }

    public IReadOnlyList<FamilySearchResult> Search(FamilySearchQuery query)
    {
        if (query is null)
        {
            throw new ArgumentNullException(nameof(query));
        }

        if (query.Limit < 1 || query.Limit > MaximumSearchLimit)
        {
            throw new ArgumentOutOfRangeException(nameof(query), "Search limit must be between 1 and 200.");
        }

        using SqliteConnection connection = OpenConnection();
        using SqliteCommand command = CreateSearchCommand(connection, query);
        using SqliteDataReader reader = command.ExecuteReader();
        List<FamilySearchResult> results = new List<FamilySearchResult>();
        while (reader.Read())
        {
            results.Add(ReadSearchResult(reader));
        }

        return results.AsReadOnly();
    }

    public void MarkMissingFiles(
        IReadOnlyCollection<string> seenPaths,
        IReadOnlyCollection<string> scannedRootPaths)
    {
        if (seenPaths is null || scannedRootPaths is null)
        {
            throw new ArgumentNullException(seenPaths is null ? nameof(seenPaths) : nameof(scannedRootPaths));
        }

        HashSet<string> seen = new HashSet<string>(
            seenPaths.Select(Path.GetFullPath),
            StringComparer.OrdinalIgnoreCase);
        string[] roots = scannedRootPaths
            .Select(NormalizeRootPath)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();
        using SqliteConnection connection = OpenConnection();
        using SqliteTransaction transaction = connection.BeginTransaction();
        foreach ((long id, string path) in ReadFamilyPaths(connection, transaction))
        {
            string fullPath = Path.GetFullPath(path);
            if (roots.Any(root => IsUnderRoot(fullPath, root)))
            {
                Execute(
                    connection,
                    transaction,
                    "UPDATE families SET is_deleted=$deleted WHERE id=$id;",
                    ("$deleted", seen.Contains(fullPath) ? 0 : 1),
                    ("$id", id));
            }
        }

        transaction.Commit();
    }

    public void Dispose()
    {
    }

    private SqliteConnection OpenConnection()
    {
        SqliteConnection connection = new SqliteConnection(_connectionString);
        connection.Open();
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = "PRAGMA foreign_keys = ON;";
        command.ExecuteNonQuery();
        return connection;
    }

    private static long UpsertFamily(
        SqliteConnection connection,
        SqliteTransaction transaction,
        FamilyMetadata metadata,
        LibraryFileCandidate file,
        ThumbnailResult thumbnail,
        DateTimeOffset indexedUtc)
    {
        const string sql = @"INSERT INTO families(
family_name, category, file_path, file_size, modified_utc, revit_version,
thumbnail_path, status, discipline, indexed_utc, is_deleted)
VALUES($name, $category, $path, $size, $modified, $version, $thumbnail, $status, $discipline, $indexed, 0)
ON CONFLICT(file_path) DO UPDATE SET family_name=$name, category=$category, file_size=$size,
modified_utc=$modified, revit_version=$version, thumbnail_path=$thumbnail, status=$status,
discipline=$discipline, indexed_utc=$indexed, last_error=NULL, is_deleted=0;";
        Execute(connection, transaction, sql,
            ("$name", metadata.DisplayName), ("$category", metadata.Category), ("$path", file.FilePath),
            ("$size", file.FileSize), ("$modified", FormatTimestamp(file.ModifiedUtc)),
            ("$version", metadata.RevitVersion), ("$thumbnail", thumbnail.FilePath),
            ("$status", metadata.Status), ("$discipline", metadata.Discipline),
            ("$indexed", FormatTimestamp(indexedUtc)));
        return GetFamilyId(connection, transaction, file.FilePath);
    }

    private static void ReplaceDetails(
        SqliteConnection connection,
        SqliteTransaction transaction,
        long familyId,
        FamilyMetadata metadata)
    {
        Execute(connection, transaction, "DELETE FROM family_types WHERE family_id=$id;", ("$id", familyId));
        Execute(connection, transaction, "DELETE FROM parameters WHERE family_id=$id;", ("$id", familyId));
        Execute(connection, transaction, "DELETE FROM family_tags WHERE family_id=$id;", ("$id", familyId));
        foreach (string typeName in metadata.TypeNames)
        {
            Execute(connection, transaction, "INSERT OR IGNORE INTO family_types(family_id,type_name) VALUES($id,$name);", ("$id", familyId), ("$name", typeName));
        }

        foreach (FamilyParameter parameter in metadata.Parameters)
        {
            InsertParameter(connection, transaction, familyId, parameter);
        }

        foreach (string tag in metadata.Tags)
        {
            InsertTag(connection, transaction, familyId, tag);
        }
    }

    private static void InsertParameter(
        SqliteConnection connection,
        SqliteTransaction transaction,
        long familyId,
        FamilyParameter parameter)
    {
        Execute(connection, transaction, @"INSERT INTO parameters(
family_id, parameter_name, parameter_value, storage_type, is_type_parameter)
VALUES($id,$name,$value,$storage,$isType);", ("$id", familyId), ("$name", parameter.Name),
            ("$value", parameter.Value), ("$storage", parameter.StorageType),
            ("$isType", parameter.IsTypeParameter ? 1 : 0));
    }

    private static void InsertTag(
        SqliteConnection connection,
        SqliteTransaction transaction,
        long familyId,
        string tag)
    {
        Execute(connection, transaction, "INSERT OR IGNORE INTO tags(name) VALUES($name);", ("$name", tag));
        Execute(connection, transaction, @"INSERT OR IGNORE INTO family_tags(family_id,tag_id)
SELECT $id,id FROM tags WHERE name=$name;", ("$id", familyId), ("$name", tag));
    }

    private static SqliteCommand CreateSearchCommand(SqliteConnection connection, FamilySearchQuery query)
    {
        SqliteCommand command = connection.CreateCommand();
        command.CommandText = @"SELECT f.id,f.family_name,f.file_path,f.category,f.status,f.discipline,f.thumbnail_path
FROM families f WHERE f.is_deleted=0
AND ($category IS NULL OR f.category=$category)
AND ($status IS NULL OR f.status=$status)
AND ($discipline IS NULL OR f.discipline=$discipline)
AND ($text IS NULL OR f.family_name LIKE $text ESCAPE '\'
 OR COALESCE(f.category,'') LIKE $text ESCAPE '\'
 OR EXISTS(SELECT 1 FROM family_types ft WHERE ft.family_id=f.id AND ft.type_name LIKE $text ESCAPE '\')
 OR EXISTS(SELECT 1 FROM parameters p WHERE p.family_id=f.id AND (p.parameter_name LIKE $text ESCAPE '\' OR COALESCE(p.parameter_value,'') LIKE $text ESCAPE '\'))
 OR EXISTS(SELECT 1 FROM family_tags fj JOIN tags t ON t.id=fj.tag_id WHERE fj.family_id=f.id AND t.name LIKE $text ESCAPE '\'))
ORDER BY f.family_name COLLATE NOCASE, f.file_path COLLATE NOCASE LIMIT $limit;";
        command.Parameters.AddWithValue("$category", DatabaseValue(query.Category));
        command.Parameters.AddWithValue("$status", DatabaseValue(query.Status));
        command.Parameters.AddWithValue("$discipline", DatabaseValue(query.Discipline));
        command.Parameters.AddWithValue("$text", DatabaseValue(CreateLikePattern(query.Text)));
        command.Parameters.AddWithValue("$limit", query.Limit);
        return command;
    }

    private static FamilySearchResult ReadSearchResult(SqliteDataReader reader)
    {
        return new FamilySearchResult(
            reader.GetInt64(0), reader.GetString(1), reader.GetString(2),
            GetNullableString(reader, 3), GetNullableString(reader, 4),
            GetNullableString(reader, 5), GetNullableString(reader, 6));
    }

    private static long GetFamilyId(SqliteConnection connection, SqliteTransaction transaction, string path)
    {
        using SqliteCommand command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = "SELECT id FROM families WHERE file_path=$path;";
        command.Parameters.AddWithValue("$path", path);
        return Convert.ToInt64(command.ExecuteScalar(), CultureInfo.InvariantCulture);
    }

    private static void Execute(
        SqliteConnection connection,
        SqliteTransaction transaction,
        string sql,
        params (string Name, object? Value)[] parameters)
    {
        using SqliteCommand command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = sql;
        foreach ((string name, object? value) in parameters)
        {
            command.Parameters.AddWithValue(name, DatabaseValue(value));
        }

        command.ExecuteNonQuery();
    }

    private static void ValidateUpsert(FamilyMetadata metadata, LibraryFileCandidate file, ThumbnailResult thumbnail)
    {
        if (metadata is null || file is null || thumbnail is null)
        {
            throw new ArgumentNullException(metadata is null ? nameof(metadata) : file is null ? nameof(file) : nameof(thumbnail));
        }

        if (!string.Equals(metadata.SourcePath, file.FilePath, StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("Metadata source path must match the scanned file path.", nameof(metadata));
        }
    }

    private static string ValidateFilePath(string filePath)
    {
        return string.IsNullOrWhiteSpace(filePath)
            ? throw new ArgumentException("A file path is required.", nameof(filePath))
            : filePath;
    }

    private static IReadOnlyList<(long Id, string Path)> ReadFamilyPaths(
        SqliteConnection connection,
        SqliteTransaction transaction)
    {
        using SqliteCommand command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = "SELECT id, file_path FROM families;";
        using SqliteDataReader reader = command.ExecuteReader();
        List<(long Id, string Path)> paths = new List<(long Id, string Path)>();
        while (reader.Read())
        {
            paths.Add((reader.GetInt64(0), reader.GetString(1)));
        }

        return paths;
    }

    private static string NormalizeRootPath(string rootPath)
    {
        string fullPath = Path.GetFullPath(ValidateFilePath(rootPath));
        return fullPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    }

    private static bool IsUnderRoot(string filePath, string rootPath)
    {
        if (string.Equals(filePath, rootPath, StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        string prefix = rootPath + Path.DirectorySeparatorChar;
        return filePath.StartsWith(prefix, StringComparison.OrdinalIgnoreCase);
    }

    private static string FormatTimestamp(DateTimeOffset value)
    {
        return value.ToUniversalTime().ToString("O", CultureInfo.InvariantCulture);
    }

    private static DateTimeOffset ParseTimestamp(string value)
    {
        return DateTimeOffset.Parse(value, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind);
    }

    private static object DatabaseValue(object? value)
    {
        return value ?? DBNull.Value;
    }

    private static string? GetNullableString(SqliteDataReader reader, int ordinal)
    {
        return reader.IsDBNull(ordinal) ? null : reader.GetString(ordinal);
    }

    private static string? CreateLikePattern(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return null;
        }

        string escaped = value!.Trim().Replace("\\", "\\\\").Replace("%", "\\%").Replace("_", "\\_");
        return "%" + escaped + "%";
    }
}
