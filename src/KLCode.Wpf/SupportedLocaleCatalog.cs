using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace KLCode.Wpf;

public static class SupportedLocaleCatalog
{
    public const string FallbackLocale = "en_us";

    private static readonly ReadOnlyCollection<string> LocaleValues =
        Array.AsReadOnly(new[]
        {
            FallbackLocale,
            "ko",
            "fr_fr",
            "ru",
            "chinese_s",
            "es_es",
            "de_de",
            "pt_br",
        });

    public static IReadOnlyList<string> All => LocaleValues;

    public static string SelectAvailableLocale(
        string? requestedLocale,
        IEnumerable<string> availableLocales)
    {
        if (availableLocales is null)
        {
            throw new ArgumentNullException(nameof(availableLocales));
        }

        HashSet<string> available = new HashSet<string>(StringComparer.Ordinal);
        foreach (string? availableLocale in availableLocales)
        {
            if (string.IsNullOrWhiteSpace(availableLocale))
            {
                throw new ArgumentException(
                    "Available locale entries must be non-empty.",
                    nameof(availableLocales));
            }

            available.Add(Normalize(availableLocale));
        }
        if (!available.Contains(FallbackLocale))
        {
            throw new InvalidOperationException(
                "The English design-system resource dictionary is required as the fallback.");
        }

        string requested = Normalize(requestedLocale);
        return LocaleValues.Contains(requested) && available.Contains(requested)
            ? requested
            : FallbackLocale;
    }

    private static string Normalize(string? locale)
    {
        if (string.IsNullOrWhiteSpace(locale))
        {
            return FallbackLocale;
        }

        string normalized = locale!.Trim().Replace('-', '_').ToLowerInvariant();
        return normalized switch
        {
            "ko_kr" => "ko",
            "ru_ru" => "ru",
            "zh_cn" => "chinese_s",
            "zh_hans" => "chinese_s",
            _ => normalized,
        };
    }
}
