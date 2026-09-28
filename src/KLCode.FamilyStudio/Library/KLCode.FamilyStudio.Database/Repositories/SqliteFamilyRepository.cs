using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using KLCode.FamilyStudio.Core.Configuration;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;
using KLCode.FamilyStudio.Core.Repositories;
using KLCode.FamilyStudio.Core.Search;
using KLCode.FamilyStudio.Database.Migrations;
using Microsoft.Data.Sqlite;
using SQLitePCL;

namespace KLCode.FamilyStudio.Database.Repositories;

public sealed class SqliteFamilyRepository : IFamilyRepository, IDisposable
{
    private const int MaximumSearchLimit = 200;
    private const string SearchResultColumns = @"f.id,f.family_name,f.file_path,f.category,f.status,f.discipline,f.thumbnail_path,
(SELECT COUNT(*) FROM families exact_copy
 WHERE exact_copy.is_deleted=0 AND f.file_hash IS NOT NULL AND exact_copy.file_hash=f.file_hash),
(SELECT COUNT(DISTINCT COALESCE(name_variant.file_hash,name_variant.file_path)) FROM families name_variant
 WHERE name_variant.is_deleted=0 AND name_variant.family_name=f.family_name),
f.file_hash,f.modified_utc,f.revit_version";
    private readonly string _connectionString;

    static SqliteFamilyRepository()
    {
        // Microsoft.Data.Sqlite does not choose a SQLite provider automatically
        // when this library is loaded inside Revit's .NET Framework process.
        AppDomain.CurrentDomain.AssemblyResolve += ResolveSqliteDependency;
        LoadBundledSqliteNativeLibrary();
        raw.SetProvider(new SQLite3Provider_e_sqlite3());
        raw.FreezeProvider();
    }

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
            Mode = SqliteOpenMode.ReadWriteCreate,
            Pooling = false
        }.ToString();
        using SqliteConnection connection = OpenConnection();
        SqliteMigrationRunner.Apply(connection);
    }

    public IndexedFileState? GetIndexedFile(string filePath)
    {
        using SqliteConnection connection = OpenConnection();
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = @"SELECT file_path, file_size, modified_utc, file_hash, thumbnail_path
FROM families WHERE file_path = $path AND is_deleted = 0;";
        command.Parameters.AddWithValue("$path", ValidateFilePath(filePath));
        using SqliteDataReader reader = command.ExecuteReader();
        return reader.Read()
            ? new IndexedFileState(reader.GetString(0), reader.GetInt64(1), ParseTimestamp(reader.GetString(2)), GetNullableString(reader, 3), GetNullableString(reader, 4))
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
        ReplaceDetails(connection, transaction, familyId, metadata, thumbnail);
        transaction.Commit();
    }

    public void SyncLibraryRoots(IReadOnlyList<LibraryRoot> roots)
    {
        if (roots is null)
        {
            throw new ArgumentNullException(nameof(roots));
        }

        using SqliteConnection connection = OpenConnection();
        using SqliteTransaction transaction = connection.BeginTransaction();
        Execute(connection, transaction, "DELETE FROM library_roots;");
        foreach (LibraryRoot root in roots)
        {
            Execute(connection, transaction, @"INSERT INTO library_roots(root_path,enabled,discipline,default_status)
VALUES($path,$enabled,$discipline,$status);",
                ("$path", NormalizeRootPath(root.Path)),
                ("$enabled", root.IsEnabled ? 1 : 0),
                ("$discipline", root.Discipline),
                ("$status", root.DefaultStatus));
        }

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

    public FamilyCatalogFilterOptions GetFilterOptions()
    {
        using SqliteConnection connection = OpenConnection();
        return new FamilyCatalogFilterOptions(
            ReadDistinctStrings(connection, @"SELECT DISTINCT category FROM families
WHERE is_deleted=0 AND category IS NOT NULL ORDER BY category COLLATE NOCASE;"),
            ReadDistinctStrings(connection, @"SELECT DISTINCT ft.type_name FROM family_types ft
JOIN families f ON f.id=ft.family_id WHERE f.is_deleted=0 ORDER BY ft.type_name COLLATE NOCASE;"),
            ReadDistinctStrings(connection, @"SELECT DISTINCT p.parameter_name FROM parameters p
JOIN families f ON f.id=p.family_id WHERE f.is_deleted=0 ORDER BY p.parameter_name COLLATE NOCASE;"),
            ReadDistinctStrings(connection, @"SELECT root_path FROM library_roots WHERE enabled=1
ORDER BY root_path COLLATE NOCASE;"));
    }

    public FamilyDetail? GetDetail(long familyId)
    {
        ValidateFamilyId(familyId);
        using SqliteConnection connection = OpenConnection();
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = "SELECT " + SearchResultColumns + @",
EXISTS(SELECT 1 FROM family_favorites ff WHERE ff.family_id=f.id),
(SELECT last_used_utc FROM family_recent_use fru WHERE fru.family_id=f.id)
FROM families f WHERE f.id=$id AND f.is_deleted=0;";
        command.Parameters.AddWithValue("$id", familyId);
        using SqliteDataReader reader = command.ExecuteReader();
        if (!reader.Read())
        {
            return null;
        }

        FamilySearchResult summary = ReadSearchResult(reader);
        bool isFavorite = reader.GetInt64(12) == 1;
        DateTimeOffset? lastUsedUtc = GetNullableString(reader, 13) is string timestamp ? ParseTimestamp(timestamp) : null;
        return new FamilyDetail(
            summary,
            ReadTypeDetails(connection, familyId),
            ReadParameters(connection, familyId, null),
            ReadStringColumn(connection, @"SELECT t.name FROM tags t
JOIN family_tags ft ON ft.tag_id=t.id WHERE ft.family_id=$id ORDER BY t.name COLLATE NOCASE;", familyId),
            isFavorite,
            lastUsedUtc);
    }

    public void SetFavorite(long familyId, bool isFavorite)
    {
        ValidateFamilyId(familyId);
        using SqliteConnection connection = OpenConnection();
        EnsureActiveFamilyExists(connection, familyId);
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = isFavorite
            ? "INSERT OR IGNORE INTO family_favorites(family_id,created_utc) VALUES($id,$created);"
            : "DELETE FROM family_favorites WHERE family_id=$id;";
        command.Parameters.AddWithValue("$id", familyId);
        if (isFavorite)
        {
            command.Parameters.AddWithValue("$created", FormatTimestamp(DateTimeOffset.UtcNow));
        }

        command.ExecuteNonQuery();
    }

    public IReadOnlyList<FamilySearchResult> GetFavorites(int limit)
    {
        return ReadPinnedResults(
            "SELECT " + SearchResultColumns + @"
FROM families f JOIN family_favorites ff ON ff.family_id=f.id
WHERE f.is_deleted=0 ORDER BY ff.created_utc DESC, f.family_name COLLATE NOCASE LIMIT $limit;",
            limit);
    }

    public void RecordUse(long familyId, FamilyUseAction action, DateTimeOffset usedUtc)
    {
        ValidateFamilyId(familyId);
        using SqliteConnection connection = OpenConnection();
        EnsureActiveFamilyExists(connection, familyId);
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = @"INSERT INTO family_recent_use(family_id,last_action,last_used_utc)
VALUES($id,$action,$timestamp)
ON CONFLICT(family_id) DO UPDATE SET last_action=$action,last_used_utc=$timestamp;";
        command.Parameters.AddWithValue("$id", familyId);
        command.Parameters.AddWithValue("$action", action.ToString());
        command.Parameters.AddWithValue("$timestamp", FormatTimestamp(usedUtc));
        command.ExecuteNonQuery();
    }

    public IReadOnlyList<FamilySearchResult> GetRecent(int limit)
    {
        return ReadPinnedResults(
            "SELECT " + SearchResultColumns + @"
FROM families f JOIN family_recent_use fru ON fru.family_id=f.id
WHERE f.is_deleted=0 ORDER BY fru.last_used_utc DESC, f.family_name COLLATE NOCASE LIMIT $limit;",
            limit);
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

    private static void LoadBundledSqliteNativeLibrary()
    {
        string nativeLibraryPath = Environment.GetEnvironmentVariable("KLCODE_FAMILY_STUDIO_NATIVE_SQLITE");
        if (string.IsNullOrWhiteSpace(nativeLibraryPath))
        {
            return;
        }

        if (!File.Exists(nativeLibraryPath))
        {
            throw new FileNotFoundException("The bundled SQLite native library was not found.", nativeLibraryPath);
        }

        if (LoadLibrary(nativeLibraryPath) == IntPtr.Zero)
        {
            throw new InvalidOperationException(
                "The bundled SQLite native library could not be loaded: " +
                Marshal.GetLastWin32Error().ToString(CultureInfo.InvariantCulture));
        }
    }

    [DllImport("kernel32", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr LoadLibrary(string fileName);

    private static Assembly? ResolveSqliteDependency(object sender, ResolveEventArgs args)
    {
        AssemblyName requestedAssembly = new AssemblyName(args.Name);
        if (!string.Equals(requestedAssembly.Name, "System.Memory", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        return AppDomain.CurrentDomain.GetAssemblies()
            .FirstOrDefault(assembly => string.Equals(
                assembly.GetName().Name,
                requestedAssembly.Name,
                StringComparison.OrdinalIgnoreCase));
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
family_name, category, file_path, file_hash, file_size, modified_utc, revit_version,
thumbnail_path, status, discipline, indexed_utc, is_deleted)
VALUES($name, $category, $path, $hash, $size, $modified, $version, $thumbnail, $status, $discipline, $indexed, 0)
ON CONFLICT(file_path) DO UPDATE SET family_name=$name, category=$category, file_size=$size,
file_hash=$hash, modified_utc=$modified, revit_version=$version, thumbnail_path=$thumbnail, status=$status,
discipline=$discipline, indexed_utc=$indexed, last_error=NULL, is_deleted=0;";
        Execute(connection, transaction, sql,
            ("$name", metadata.DisplayName), ("$category", metadata.Category), ("$path", file.FilePath),
            ("$hash", file.FileHash), ("$size", file.FileSize), ("$modified", FormatTimestamp(file.ModifiedUtc)),
            ("$version", metadata.RevitVersion), ("$thumbnail", thumbnail.FilePath),
            ("$status", metadata.Status), ("$discipline", metadata.Discipline),
            ("$indexed", FormatTimestamp(indexedUtc)));
        return GetFamilyId(connection, transaction, file.FilePath);
    }

    private static void ReplaceDetails(
        SqliteConnection connection,
        SqliteTransaction transaction,
        long familyId,
        FamilyMetadata metadata,
        ThumbnailResult thumbnail)
    {
        Execute(connection, transaction, "DELETE FROM parameters WHERE family_id=$id;", ("$id", familyId));
        Execute(connection, transaction, "DELETE FROM family_tags WHERE family_id=$id;", ("$id", familyId));
        Execute(connection, transaction, "DELETE FROM family_previews WHERE family_id=$id;", ("$id", familyId));
        Execute(connection, transaction, "DELETE FROM family_types WHERE family_id=$id;", ("$id", familyId));
        Dictionary<string, long> typeIds = new Dictionary<string, long>(StringComparer.OrdinalIgnoreCase);
        foreach (string typeName in metadata.TypeNames)
        {
            typeIds[typeName] = InsertType(connection, transaction, familyId, typeName);
        }

        foreach (FamilyParameter parameter in metadata.Parameters)
        {
            InsertParameter(connection, transaction, familyId, null, parameter);
        }

        foreach (FamilyTypeMetadata type in metadata.Types)
        {
            long typeId = typeIds.TryGetValue(type.Name, out long existingTypeId)
                ? existingTypeId
                : InsertType(connection, transaction, familyId, type.Name);
            foreach (FamilyParameter parameter in type.Parameters)
            {
                InsertParameter(connection, transaction, familyId, typeId, parameter);
            }
        }

        foreach (string tag in metadata.Tags)
        {
            InsertTag(connection, transaction, familyId, tag);
        }

        foreach (FamilyPreview preview in thumbnail.Previews)
        {
            long? typeId = null;
            if (preview.TypeName is not null)
            {
                if (!typeIds.TryGetValue(preview.TypeName, out long foundTypeId))
                {
                    continue;
                }

                typeId = foundTypeId;
            }

            Execute(connection, transaction, @"INSERT INTO family_previews(family_id,type_id,preview_path)
VALUES($familyId,$typeId,$path);",
                ("$familyId", familyId),
                ("$typeId", typeId),
                ("$path", preview.FilePath));
        }
    }

    private static long InsertType(
        SqliteConnection connection,
        SqliteTransaction transaction,
        long familyId,
        string typeName)
    {
        Execute(connection, transaction, "INSERT OR IGNORE INTO family_types(family_id,type_name) VALUES($id,$name);", ("$id", familyId), ("$name", typeName));
        using SqliteCommand command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = "SELECT id FROM family_types WHERE family_id=$id AND type_name=$name;";
        command.Parameters.AddWithValue("$id", familyId);
        command.Parameters.AddWithValue("$name", typeName);
        return Convert.ToInt64(command.ExecuteScalar(), CultureInfo.InvariantCulture);
    }

    private static void InsertParameter(
        SqliteConnection connection,
        SqliteTransaction transaction,
        long familyId,
        long? typeId,
        FamilyParameter parameter)
    {
        Execute(connection, transaction, @"INSERT INTO parameters(
family_id, type_id, parameter_name, parameter_value, storage_type, is_type_parameter)
VALUES($id,$typeId,$name,$value,$storage,$isType);", ("$id", familyId), ("$typeId", typeId), ("$name", parameter.Name),
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
        command.CommandText = "SELECT " + SearchResultColumns + @"
FROM families f WHERE f.is_deleted=0
AND ($category IS NULL OR f.category=$category)
AND ($status IS NULL OR f.status=$status)
AND ($discipline IS NULL OR f.discipline=$discipline)
AND ($typeName IS NULL OR EXISTS(SELECT 1 FROM family_types ft_filter WHERE ft_filter.family_id=f.id AND ft_filter.type_name=$typeName))
AND ($parameterName IS NULL OR EXISTS(SELECT 1 FROM parameters p_filter WHERE p_filter.family_id=f.id AND p_filter.parameter_name=$parameterName))
AND ($rootPrefix IS NULL OR f.file_path LIKE $rootPrefix ESCAPE '\')
AND ($duplicatesOnly=0 OR
 EXISTS(SELECT 1 FROM families exact_match WHERE exact_match.is_deleted=0 AND f.file_hash IS NOT NULL AND exact_match.file_hash=f.file_hash AND exact_match.id<>f.id)
 OR EXISTS(SELECT 1 FROM families name_match WHERE name_match.is_deleted=0 AND name_match.family_name=f.family_name AND name_match.id<>f.id
           AND COALESCE(name_match.file_hash,name_match.file_path)<>COALESCE(f.file_hash,f.file_path)))
AND ($text IS NULL OR f.family_name LIKE $text ESCAPE '\'
 OR COALESCE(f.category,'') LIKE $text ESCAPE '\'
 OR EXISTS(SELECT 1 FROM family_types ft WHERE ft.family_id=f.id AND ft.type_name LIKE $text ESCAPE '\')
 OR EXISTS(SELECT 1 FROM parameters p WHERE p.family_id=f.id AND (p.parameter_name LIKE $text ESCAPE '\' OR COALESCE(p.parameter_value,'') LIKE $text ESCAPE '\'))
 OR EXISTS(SELECT 1 FROM family_tags fj JOIN tags t ON t.id=fj.tag_id WHERE fj.family_id=f.id AND t.name LIKE $text ESCAPE '\'))
ORDER BY f.family_name COLLATE NOCASE, f.file_path COLLATE NOCASE LIMIT $limit;";
        command.Parameters.AddWithValue("$category", DatabaseValue(query.Category));
        command.Parameters.AddWithValue("$status", DatabaseValue(query.Status));
        command.Parameters.AddWithValue("$discipline", DatabaseValue(query.Discipline));
        command.Parameters.AddWithValue("$typeName", DatabaseValue(query.TypeName));
        command.Parameters.AddWithValue("$parameterName", DatabaseValue(query.ParameterName));
        command.Parameters.AddWithValue("$rootPrefix", DatabaseValue(CreateRootLikePattern(query.RootPath)));
        command.Parameters.AddWithValue("$duplicatesOnly", query.DuplicatesOnly ? 1 : 0);
        command.Parameters.AddWithValue("$text", DatabaseValue(CreateLikePattern(query.Text)));
        command.Parameters.AddWithValue("$limit", query.Limit);
        return command;
    }

    private static FamilySearchResult ReadSearchResult(SqliteDataReader reader)
    {
        return new FamilySearchResult(
            reader.GetInt64(0), reader.GetString(1), reader.GetString(2),
            GetNullableString(reader, 3), GetNullableString(reader, 4),
            GetNullableString(reader, 5), GetNullableString(reader, 6),
            Convert.ToInt32(reader.GetInt64(7), CultureInfo.InvariantCulture),
            Convert.ToInt32(reader.GetInt64(8), CultureInfo.InvariantCulture),
            GetNullableString(reader, 9),
            ParseTimestamp(reader.GetString(10)),
            GetNullableString(reader, 11));
    }

    private IReadOnlyList<FamilySearchResult> ReadPinnedResults(string sql, int limit)
    {
        if (limit < 1 || limit > MaximumSearchLimit)
        {
            throw new ArgumentOutOfRangeException(nameof(limit), "Result limit must be between 1 and 200.");
        }

        using SqliteConnection connection = OpenConnection();
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = sql;
        command.Parameters.AddWithValue("$limit", limit);
        using SqliteDataReader reader = command.ExecuteReader();
        List<FamilySearchResult> results = new List<FamilySearchResult>();
        while (reader.Read())
        {
            results.Add(ReadSearchResult(reader));
        }

        return results.AsReadOnly();
    }

    private static IReadOnlyList<string> ReadStringColumn(SqliteConnection connection, string sql, long familyId)
    {
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = sql;
        command.Parameters.AddWithValue("$id", familyId);
        using SqliteDataReader reader = command.ExecuteReader();
        List<string> values = new List<string>();
        while (reader.Read())
        {
            values.Add(reader.GetString(0));
        }

        return values.AsReadOnly();
    }

    private static IReadOnlyList<string> ReadDistinctStrings(SqliteConnection connection, string sql)
    {
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = sql;
        using SqliteDataReader reader = command.ExecuteReader();
        List<string> values = new List<string>();
        while (reader.Read() && !reader.IsDBNull(0))
        {
            values.Add(reader.GetString(0));
        }

        return values.AsReadOnly();
    }

    private static IReadOnlyList<FamilyTypeDetail> ReadTypeDetails(SqliteConnection connection, long familyId)
    {
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = @"SELECT ft.id,ft.type_name,fp.preview_path
FROM family_types ft LEFT JOIN family_previews fp ON fp.type_id=ft.id
WHERE ft.family_id=$id ORDER BY ft.type_name COLLATE NOCASE;";
        command.Parameters.AddWithValue("$id", familyId);
        using SqliteDataReader reader = command.ExecuteReader();
        List<(long Id, string Name, string? ThumbnailPath)> types = new List<(long Id, string Name, string? ThumbnailPath)>();
        while (reader.Read())
        {
            types.Add((reader.GetInt64(0), reader.GetString(1), GetNullableString(reader, 2)));
        }

        reader.Close();

        return types
            .Select(type => new FamilyTypeDetail(type.Name, ReadParameters(connection, familyId, type.Id), type.ThumbnailPath))
            .ToArray();
    }

    private static IReadOnlyList<FamilyParameter> ReadParameters(
        SqliteConnection connection,
        long familyId,
        long? typeId)
    {
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = @"SELECT parameter_name,parameter_value,storage_type,is_type_parameter
FROM parameters WHERE family_id=$id AND " +
            (typeId.HasValue ? "type_id=$typeId" : "type_id IS NULL") +
            " ORDER BY parameter_name COLLATE NOCASE;";
        command.Parameters.AddWithValue("$id", familyId);
        if (typeId.HasValue)
        {
            command.Parameters.AddWithValue("$typeId", typeId.Value);
        }
        using SqliteDataReader reader = command.ExecuteReader();
        List<FamilyParameter> values = new List<FamilyParameter>();
        while (reader.Read())
        {
            values.Add(new FamilyParameter(
                reader.GetString(0),
                GetNullableString(reader, 1),
                GetNullableString(reader, 2),
                reader.GetInt64(3) == 1));
        }

        return values.AsReadOnly();
    }

    private static void EnsureActiveFamilyExists(SqliteConnection connection, long familyId)
    {
        using SqliteCommand command = connection.CreateCommand();
        command.CommandText = "SELECT COUNT(*) FROM families WHERE id=$id AND is_deleted=0;";
        command.Parameters.AddWithValue("$id", familyId);
        if (Convert.ToInt32(command.ExecuteScalar(), CultureInfo.InvariantCulture) != 1)
        {
            throw new ArgumentException("The family does not exist or is deleted.", nameof(familyId));
        }
    }

    private static void ValidateFamilyId(long familyId)
    {
        if (familyId <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(familyId), "A positive family id is required.");
        }
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

    private static string? CreateRootLikePattern(string? rootPath)
    {
        if (string.IsNullOrWhiteSpace(rootPath))
        {
            return null;
        }

        string root = NormalizeRootPath(rootPath!) + Path.DirectorySeparatorChar;
        return root.Replace("\\", "\\\\").Replace("%", "\\%").Replace("_", "\\_") + "%";
    }
}
