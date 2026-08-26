using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace KLA.ModelStartupImporter.Core;

internal static class StartupRowParser
{
    internal static readonly string[] RequiredHeaders =
    {
        "ItemId", "Title", "Category", "Selected", "EngineerComment", "PlacementHint",
    };

    internal static bool TryCreateHeaderMap(IReadOnlyList<string> values, out IReadOnlyDictionary<string, int> headerMap)
    {
        var map = values
            .Select((value, index) => new { Header = value.Trim(), Index = index })
            .Where(entry => entry.Header.Length > 0)
            .GroupBy(entry => entry.Header, StringComparer.OrdinalIgnoreCase)
            .Where(group => group.Count() == 1)
            .ToDictionary(group => group.Key, group => group.Single().Index, StringComparer.OrdinalIgnoreCase);
        headerMap = map;
        return RequiredHeaders.All(map.ContainsKey);
    }

    internal static StartupItem? Parse(
        IReadOnlyList<string> values,
        IReadOnlyDictionary<string, int> headerMap,
        string sourceLocation)
    {
        if (values.All(string.IsNullOrWhiteSpace))
        {
            return null;
        }

        var itemId = Value(values, headerMap, "ItemId");
        if (string.IsNullOrWhiteSpace(itemId))
        {
            throw new StartupFormatException(sourceLocation + " has content but no ItemId.");
        }

        return new StartupItem(
            itemId,
            RequiredValue(values, headerMap, "Title", sourceLocation),
            ParseCategory(RequiredValue(values, headerMap, "Category", sourceLocation), sourceLocation),
            ParseSelection(Value(values, headerMap, "Selected"), sourceLocation),
            Value(values, headerMap, "EngineerComment"),
            sourceLocation,
            Value(values, headerMap, "PlacementHint"));
    }

    private static string RequiredValue(
        IReadOnlyList<string> values,
        IReadOnlyDictionary<string, int> headerMap,
        string header,
        string sourceLocation)
    {
        var value = Value(values, headerMap, header);
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new StartupFormatException(sourceLocation + " is missing " + header + ".");
        }

        return value;
    }

    private static string Value(
        IReadOnlyList<string> values,
        IReadOnlyDictionary<string, int> headerMap,
        string header)
    {
        var index = headerMap[header];
        return index < values.Count ? values[index].Trim() : string.Empty;
    }

    private static bool ParseSelection(string value, string sourceLocation)
    {
        switch (value.Trim().ToUpperInvariant())
        {
            case "X":
            case "TRUE":
            case "YES":
            case "1":
                return true;
            case "":
            case "FALSE":
            case "NO":
            case "0":
                return false;
            default:
                throw new StartupFormatException(sourceLocation + " has an invalid selection value '" + value + "'.");
        }
    }

    private static StartupItemCategory ParseCategory(string value, string sourceLocation)
    {
        switch (value.Trim().Replace("-", " ").ToUpperInvariant())
        {
            case "DETAIL":
                return StartupItemCategory.Detail;
            case "GENERAL NOTE":
                return StartupItemCategory.GeneralNote;
            case "SCHEDULE":
                return StartupItemCategory.Schedule;
            case "OTHER":
                return StartupItemCategory.Other;
            default:
                throw new StartupFormatException(sourceLocation + " has an invalid category '" + value + "'.");
        }
    }
}
