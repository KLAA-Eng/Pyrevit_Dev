using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using KLA.ModelStartupImporter.Core;

namespace KLA.ModelStartupImporter.UI.ViewModels;

public sealed class StartupImportReviewViewModel : INotifyPropertyChanged
{
    private readonly Func<string, string> _text;
    private StartupImportReviewRow? _selectedRow;

    public StartupImportReviewViewModel(
        StartupDocumentModel document,
        StartupImportSettings settings,
        StartupImportReview review,
        Func<string, string>? text = null)
    {
        if (document is null) throw new ArgumentNullException(nameof(document));
        if (settings is null) throw new ArgumentNullException(nameof(settings));
        if (review is null) throw new ArgumentNullException(nameof(review));
        _text = text ?? StartupImporterText.Get;

        HashSet<string> actionableIds = new HashSet<string>(review.ActionableMatches.Select(match => match.Item.ItemId), StringComparer.OrdinalIgnoreCase);
        HashSet<string> existingIds = new HashSet<string>(review.ExistingMatches.Select(match => match.Item.ItemId), StringComparer.OrdinalIgnoreCase);
        List<StartupImportReviewRow> rows = new List<StartupImportReviewRow>();
        foreach (StartupItem item in document.Items)
        {
            settings.Catalog.TryGet(item.ItemId, out CatalogItem? catalogItem);
            string tone = actionableIds.Contains(item.ItemId) ? "Matched" : existingIds.Contains(item.ItemId) ? "Existing" : "Unchecked";
            rows.Add(new StartupImportReviewRow(item, catalogItem, tone, actionableIds.Contains(item.ItemId), UpdateSelection, _text));
        }

        Rows = new ObservableCollection<StartupImportReviewRow>(rows);
        MatchedSummary = string.Format(_text("MatchedSummaryFormat"), review.ActionableMatches.Count);
        ExistingSummary = string.Format(_text("ExistingSummaryFormat"), review.ExistingMatches.Count);
        UncheckedSummary = string.Format(_text("UncheckedSummaryFormat"), review.Plan.SkippedItems.Count);
        CatalogSummary = string.Format(_text("CatalogHashSummaryFormat"), settings.CatalogVersion, ShortHash(document.FileHash));
        HasBlockingIssues = review.Plan.HasBlockingIssues;
        SelectedRow = Rows.FirstOrDefault(row => row.IsActionable) ?? Rows.FirstOrDefault();
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    public ObservableCollection<StartupImportReviewRow> Rows { get; }
    public string MatchedSummary { get; }
    public string ExistingSummary { get; }
    public string UncheckedSummary { get; }
    public string CatalogSummary { get; }
    public bool HasBlockingIssues { get; }
    public int SelectedCount => Rows.Count(row => row.IsSelected);
    public bool CanImport => !HasBlockingIssues && SelectedCount > 0;
    public string SelectionStatus => string.Format(_text("WillCreateFormat"), SelectedCount);
    public string ImportButtonLabel => string.Format(
        _text(SelectedCount == 1 ? "ImportOneItemFormat" : "ImportItemsFormat"),
        SelectedCount);

    public StartupImportReviewRow? SelectedRow
    {
        get => _selectedRow;
        set
        {
            if (ReferenceEquals(_selectedRow, value)) return;
            _selectedRow = value;
            Notify();
        }
    }

    public void SelectAll()
    {
        foreach (StartupImportReviewRow row in Rows.Where(row => row.IsActionable)) row.IsSelected = true;
        UpdateSelection();
    }

    public void SelectNone()
    {
        foreach (StartupImportReviewRow row in Rows.Where(row => row.IsActionable)) row.IsSelected = false;
        UpdateSelection();
    }

    public string[] GetSelectedItemIds()
    {
        return Rows.Where(row => row.IsActionable && row.IsSelected).Select(row => row.ItemId).ToArray();
    }

    private void UpdateSelection()
    {
        Notify(nameof(SelectedCount));
        Notify(nameof(CanImport));
        Notify(nameof(SelectionStatus));
        Notify(nameof(ImportButtonLabel));
    }

    private void Notify([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }

    private static string ShortHash(string hash)
    {
        return hash.Length <= 8 ? hash : hash.Substring(0, 4) + "…" + hash.Substring(hash.Length - 2, 2);
    }
}

public sealed class StartupImportReviewRow : INotifyPropertyChanged
{
    private readonly Action _selectionChanged;
    private bool _isSelected;

    internal StartupImportReviewRow(
        StartupItem item,
        CatalogItem? catalogItem,
        string statusTone,
        bool isActionable,
        Action selectionChanged,
        Func<string, string> text)
    {
        _selectionChanged = selectionChanged ?? throw new ArgumentNullException(nameof(selectionChanged));
        if (text is null) throw new ArgumentNullException(nameof(text));
        ItemId = item.ItemId;
        Title = item.Title;
        Category = item.Category == StartupItemCategory.GeneralNote ? "General Note" : item.Category.ToString();
        StatusTone = statusTone;
        Status = text(statusTone + "StatusLabel");
        IsActionable = isActionable;
        _isSelected = isActionable;
        TargetName = catalogItem?.TargetName ?? text("NoTargetLabel");
        SourceName = catalogItem?.SourceViewName ?? text("NoSourceLabel");
        TargetKind = catalogItem?.ContentType == StartupItemCategory.Schedule
            ? text("ScheduleTargetLabel")
            : text("DraftingViewTargetLabel");
        string[] requirements = catalogItem is null
            ? Array.Empty<string>()
            : catalogItem.RequiredTextTypeNames.Concat(catalogItem.RequiredLineStyleNames).ToArray();
        Requirements = requirements.Length == 0
            ? text("NoRequirementsLabel")
            : string.Join(", ", requirements);
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    public string ItemId { get; }
    public string Title { get; }
    public string Category { get; }
    public string Status { get; }
    public string StatusTone { get; }
    public bool IsActionable { get; }
    public string TargetName { get; }
    public string SourceName { get; }
    public string TargetKind { get; }
    public string Requirements { get; }

    public bool IsSelected
    {
        get => _isSelected;
        set
        {
            if (!IsActionable || _isSelected == value) return;
            _isSelected = value;
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(IsSelected)));
            _selectionChanged();
        }
    }
}
