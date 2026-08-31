using System;
using Microsoft.Data.Sqlite;

namespace KLCode.FamilyStudio.Database.Migrations;

internal static class SqliteMigrationRunner
{
    private const int CurrentVersion = 3;

    public static void Apply(SqliteConnection connection)
    {
        using SqliteCommand versionCommand = connection.CreateCommand();
        versionCommand.CommandText = "PRAGMA user_version;";
        int version = Convert.ToInt32(versionCommand.ExecuteScalar());
        if (version > CurrentVersion)
        {
            throw new InvalidOperationException("The Family Studio database schema is newer than this application.");
        }

        if (version == 0)
        {
            ApplyVersionOne(connection);
            version = 1;
        }

        if (version == 1)
        {
            ApplyVersionTwo(connection);
            version = 2;
        }

        if (version == 2)
        {
            ApplyVersionThree(connection);
        }
    }

    private static void ApplyVersionOne(SqliteConnection connection)
    {
        using SqliteTransaction transaction = connection.BeginTransaction();
        using SqliteCommand command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = SchemaVersionOne;
        command.ExecuteNonQuery();
        transaction.Commit();
    }

    private const string SchemaVersionOne = @"
CREATE TABLE families(
  id INTEGER PRIMARY KEY,
  content_kind TEXT NOT NULL DEFAULT 'family' CHECK(content_kind = 'family'),
  family_name TEXT NOT NULL,
  category TEXT,
  file_path TEXT NOT NULL UNIQUE,
  file_hash TEXT,
  file_size INTEGER NOT NULL CHECK(file_size >= 0),
  modified_utc TEXT NOT NULL,
  revit_version TEXT,
  thumbnail_path TEXT,
  status TEXT,
  discipline TEXT,
  indexed_utc TEXT NOT NULL,
  last_error TEXT,
  is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0, 1))
);
CREATE TABLE family_types(
  id INTEGER PRIMARY KEY,
  family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
  type_name TEXT NOT NULL,
  UNIQUE(family_id, type_name)
);
CREATE TABLE parameters(
  id INTEGER PRIMARY KEY,
  family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
  type_id INTEGER REFERENCES family_types(id) ON DELETE CASCADE,
  parameter_name TEXT NOT NULL,
  parameter_value TEXT,
  storage_type TEXT,
  is_type_parameter INTEGER NOT NULL DEFAULT 0 CHECK(is_type_parameter IN (0, 1))
);
CREATE TABLE tags(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE family_tags(
  family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY(family_id, tag_id)
);
CREATE TABLE library_roots(
  id INTEGER PRIMARY KEY,
  root_path TEXT NOT NULL UNIQUE,
  enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0, 1)),
  discipline TEXT,
  default_status TEXT,
  last_scan_utc TEXT
);
CREATE TABLE index_runs(
  id INTEGER PRIMARY KEY,
  started_utc TEXT NOT NULL,
  finished_utc TEXT,
  files_seen INTEGER NOT NULL DEFAULT 0,
  files_updated INTEGER NOT NULL DEFAULT 0,
  files_skipped INTEGER NOT NULL DEFAULT 0,
  files_failed INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX ix_families_name ON families(family_name);
CREATE INDEX ix_families_filters ON families(category, status, discipline, is_deleted);
PRAGMA user_version = 1;";

    private static void ApplyVersionTwo(SqliteConnection connection)
    {
        using SqliteTransaction transaction = connection.BeginTransaction();
        using SqliteCommand command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = @"
CREATE TABLE family_favorites(
  family_id INTEGER PRIMARY KEY REFERENCES families(id) ON DELETE CASCADE,
  created_utc TEXT NOT NULL
);
CREATE TABLE family_recent_use(
  family_id INTEGER PRIMARY KEY REFERENCES families(id) ON DELETE CASCADE,
  last_action TEXT NOT NULL,
  last_used_utc TEXT NOT NULL
);
CREATE INDEX ix_family_recent_use_timestamp ON family_recent_use(last_used_utc DESC);
PRAGMA user_version = 2;";
        command.ExecuteNonQuery();
        transaction.Commit();
    }

    private static void ApplyVersionThree(SqliteConnection connection)
    {
        using SqliteTransaction transaction = connection.BeginTransaction();
        using SqliteCommand command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = @"
CREATE TABLE family_previews(
  id INTEGER PRIMARY KEY,
  family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
  type_id INTEGER REFERENCES family_types(id) ON DELETE CASCADE,
  preview_path TEXT NOT NULL,
  UNIQUE(family_id, type_id)
);
CREATE INDEX ix_family_previews_family ON family_previews(family_id);
PRAGMA user_version = 3;";
        command.ExecuteNonQuery();
        transaction.Commit();
    }
}
