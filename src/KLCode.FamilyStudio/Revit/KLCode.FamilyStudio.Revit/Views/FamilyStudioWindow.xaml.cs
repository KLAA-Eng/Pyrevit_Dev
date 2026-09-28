using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Repositories;
using KLCode.FamilyStudio.Core.Search;
using KLCode.FamilyStudio.Revit.Services;
using KLCode.Wpf;
using KLCode.Wpf.Views;

namespace KLCode.FamilyStudio.Revit.Views;

public sealed partial class FamilyStudioWindow : Window
{
    private readonly IFamilyRepository _repository;
    private readonly IFamilyLoadService _loadService;
    private readonly Func<IndexRunSummary?>? _refreshIndex;
    private readonly Dictionary<long, FamilySearchResult> _visibleFamilies = new Dictionary<long, FamilySearchResult>();
    private readonly HashSet<long> _checkedFamilyIds = new HashSet<long>();
    private bool _suppressFilterRefresh;
    private bool _suppressSelectionSync;
    private FamilyDetail? _selectedDetail;
    private long? _selectedFamilyId;

    internal FamilySearchResult? PlacementFamily { get; private set; }

    internal FamilyStudioWindow(
        IFamilyRepository repository,
        IFamilyLoadService loadService,
        Func<IndexRunSummary?>? refreshIndex)
    {
        _repository = repository ?? throw new ArgumentNullException(nameof(repository));
        _loadService = loadService ?? throw new ArgumentNullException(nameof(loadService));
        _refreshIndex = refreshIndex;
        ThemeBootstrapper.Apply(Resources, CultureInfo.CurrentUICulture.Name);
        FamilyStudioText.ApplyToolStrings(Resources);
        InitializeComponent();
        LoadFilterOptions();
        Search();
        UpdateViewMode();
    }

    private void OnHeaderMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.LeftButton == MouseButtonState.Pressed)
        {
            DragMove();
        }
    }

    private void OnCloseClick(object sender, RoutedEventArgs e) => Close();
    private void OnSearchClick(object sender, RoutedEventArgs e) => Search();
    private void OnFavoritesClick(object sender, RoutedEventArgs e) => SetResults(_repository.GetFavorites(200));
    private void OnRecentClick(object sender, RoutedEventArgs e) => SetResults(_repository.GetRecent(200));
    private void OnRefreshClick(object sender, RoutedEventArgs e) => RefreshIndex();
    private void OnLoadClick(object sender, RoutedEventArgs e) => RunSelected(false);
    private void OnLoadAndPlaceClick(object sender, RoutedEventArgs e) => RunSelected(true);
    private void OnFavoriteClick(object sender, RoutedEventArgs e) => ToggleFavorite();
    private void OnCopyPathClick(object sender, RoutedEventArgs e) => CopyPath();
    private void OnOpenFolderClick(object sender, RoutedEventArgs e) => OpenFolder();
    private void OnTypeSelectionChanged(object sender, SelectionChangedEventArgs e) => UpdateTypeDetail();

    private void OnSearchBoxKeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter)
        {
            Search();
        }
    }

    private void OnFilterChanged(object sender, RoutedEventArgs e)
    {
        if (!_suppressFilterRefresh)
        {
            Search();
        }
    }

    private void OnViewModeChanged(object sender, RoutedEventArgs e)
    {
        if (Results is not null && GridResults is not null)
        {
            UpdateViewMode();
        }
    }

    private void UpdateViewMode()
    {
        bool showGrid = GridMode.IsChecked == true;
        Results.Visibility = showGrid ? Visibility.Collapsed : Visibility.Visible;
        GridResults.Visibility = showGrid ? Visibility.Visible : Visibility.Collapsed;
        SynchronizeSelection(_selectedFamilyId);
    }

    private void OnClearFiltersClick(object sender, RoutedEventArgs e)
    {
        _suppressFilterRefresh = true;
        SearchBox.Clear();
        CategoryFilter.SelectedIndex = 0;
        TypeFilter.SelectedIndex = 0;
        ParameterFilter.SelectedIndex = 0;
        RootFilter.SelectedIndex = 0;
        DuplicatesOnly.IsChecked = false;
        _suppressFilterRefresh = false;
        Search();
    }

    private void OnResultsSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        HandleSelectionChanged(Results.SelectedItem as FamilyResultItem);
    }

    private void OnGridResultsSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        HandleSelectionChanged(GridResults.SelectedItem as FamilyResultItem);
    }

    private void HandleSelectionChanged(FamilyResultItem? item)
    {
        if (_suppressSelectionSync)
        {
            return;
        }

        _selectedFamilyId = item?.Id;
        SynchronizeSelection(_selectedFamilyId);
        UpdateDetail();
    }

    private void SynchronizeSelection(long? familyId)
    {
        _suppressSelectionSync = true;
        try
        {
            FamilyResultItem? item = familyId.HasValue
                ? Results.Items.Cast<FamilyResultItem>().FirstOrDefault(result => result.Id == familyId.Value)
                : null;
            Results.SelectedItem = item;
            GridResults.SelectedItem = item;
        }
        finally
        {
            _suppressSelectionSync = false;
        }
    }

    private void OnBatchChecked(object sender, RoutedEventArgs e)
    {
        if (sender is CheckBox { Tag: long id })
        {
            _checkedFamilyIds.Add(id);
            UpdateBatchCount();
        }
    }

    private void OnBatchUnchecked(object sender, RoutedEventArgs e)
    {
        if (sender is CheckBox { Tag: long id })
        {
            _checkedFamilyIds.Remove(id);
            UpdateBatchCount();
        }
    }

    private void OnBatchLoadClick(object sender, RoutedEventArgs e)
    {
        FamilySearchResult[] families = _checkedFamilyIds
            .Where(_visibleFamilies.ContainsKey)
            .Select(id => _visibleFamilies[id])
            .ToArray();
        if (families.Length == 0)
        {
            ShowWarning(FamilyStudioText.Get("SelectFamilyFirstLabel"));
            return;
        }

        try
        {
            _loadService.LoadBatch(families);
            foreach (FamilySearchResult family in families)
            {
                _repository.RecordUse(family.Id, FamilyUseAction.Loaded, DateTimeOffset.UtcNow);
            }

            _checkedFamilyIds.Clear();
            foreach (FamilyResultItem item in Results.Items)
            {
                item.IsChecked = false;
            }
            UpdateBatchCount();
            UpdateDetail();
        }
        catch (Exception exception)
        {
            ShowWarning(exception.Message);
        }
    }

    private void LoadFilterOptions()
    {
        _suppressFilterRefresh = true;
        try
        {
            FamilyCatalogFilterOptions options = _repository.GetFilterOptions();
            SetFilterItems(CategoryFilter, FamilyStudioText.Get("AllCategoriesLabel"), options.Categories);
            SetFilterItems(TypeFilter, FamilyStudioText.Get("AllTypesLabel"), options.TypeNames);
            SetFilterItems(ParameterFilter, FamilyStudioText.Get("AllParametersLabel"), options.ParameterNames);
            SetFilterItems(RootFilter, FamilyStudioText.Get("AllRootsLabel"), options.RootPaths);
        }
        finally
        {
            _suppressFilterRefresh = false;
        }
    }

    private static void SetFilterItems(ComboBox box, string allLabel, IReadOnlyList<string> values)
    {
        List<string> options = new List<string> { allLabel };
        options.AddRange(values);
        box.ItemsSource = options;
        box.SelectedIndex = 0;
    }

    private void Search()
    {
        SetResults(_repository.Search(new FamilySearchQuery(
            SearchBox.Text,
            SelectedFilterValue(CategoryFilter),
            null,
            null,
            SelectedFilterValue(TypeFilter),
            SelectedFilterValue(ParameterFilter),
            SelectedFilterValue(RootFilter),
            DuplicatesOnly.IsChecked == true,
            200)));
    }

    private static string? SelectedFilterValue(ComboBox box)
    {
        return box.SelectedIndex <= 0 ? null : box.SelectedItem as string;
    }

    private void SetResults(IReadOnlyList<FamilySearchResult> families)
    {
        _visibleFamilies.Clear();
        foreach (FamilySearchResult family in families)
        {
            _visibleFamilies.Add(family.Id, family);
        }

        _checkedFamilyIds.Clear();
        FamilyResultItem[] items = families.Select(family => new FamilyResultItem(family)).ToArray();
        Results.ItemsSource = items;
        GridResults.ItemsSource = items;
        _selectedFamilyId = items.Length > 0 ? items[0].Id : null;
        SynchronizeSelection(_selectedFamilyId);
        ResultCount.Text = string.Format(
            FamilyStudioText.Get(families.Count == 1 ? "ResultCountSingularFormat" : "ResultCountFormat"),
            families.Count);
        EmptyState.Visibility = families.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
        Results.Opacity = families.Count == 0 ? 0 : 1;
        GridResults.Opacity = families.Count == 0 ? 0 : 1;
        UpdateBatchCount();
        UpdateDetail();
    }

    private void UpdateBatchCount()
    {
        BatchCount.Text = string.Format(FamilyStudioText.Get("BatchCountFormat"), _checkedFamilyIds.Count);
        BatchLoadButton.Content = string.Format(FamilyStudioText.Get("BatchLoadCountFormat"), _checkedFamilyIds.Count);
        BatchLoadButton.IsEnabled = _checkedFamilyIds.Count > 0;
    }

    private FamilySearchResult? GetSelectedFamily()
    {
        return _selectedFamilyId.HasValue && _visibleFamilies.TryGetValue(_selectedFamilyId.Value, out FamilySearchResult? family)
            ? family
            : null;
    }

    private void UpdateDetail()
    {
        FamilySearchResult? selected = GetSelectedFamily();
        if (selected is null)
        {
            ClearDetail(FamilyStudioText.Get("SelectFamilyDetailsLabel"));
            return;
        }

        FamilyDetail? detail = _repository.GetDetail(selected.Id);
        if (detail is null)
        {
            ClearDetail(FamilyStudioText.Get("IndexedFamilyMissingLabel"));
            return;
        }

        _selectedDetail = detail;
        FamilyNameText.Text = detail.Summary.FamilyName;
        string unavailable = FamilyStudioText.Get("UnavailableValue");
        StatusText.Text = detail.Summary.Status ?? unavailable;
        bool approved = string.Equals(detail.Summary.Status, "Approved", StringComparison.OrdinalIgnoreCase);
        StatusChip.Style = (Style)FindResource(approved ? "KlaInfoChipStyle" : "KlaWarningChipStyle");
        StatusText.Foreground = (Brush)FindResource(approved ? "KlaInfoBrush" : "KlaWarningBrush");
        CategoryText.Text = detail.Summary.Category ?? unavailable;
        DisciplineText.Text = detail.Summary.Discipline ?? unavailable;
        Types.ItemsSource = detail.Types;
        Types.SelectedIndex = detail.Types.Count > 0 ? 0 : -1;
        Tags.ItemsSource = detail.Tags.Count > 0 ? detail.Tags : new[] { FamilyStudioText.Get("NoTagsLabel") };
        InstanceParameters.ItemsSource = detail.Parameters;
        PathText.Text = string.Format(FamilyStudioText.Get("DetailPathFormat"), detail.Summary.FilePath);
        ModifiedText.Text = string.Format(
            FamilyStudioText.Get("ModifiedVersionFormat"),
            detail.Summary.ModifiedUtc.HasValue ? detail.Summary.ModifiedUtc.Value.LocalDateTime.ToString("g") : unavailable,
            detail.Summary.RevitVersion ?? unavailable);
        CatalogCheckText.Text = string.Format(FamilyStudioText.Get("DetailCatalogCheckFormat"), detail.Summary.DuplicateLabel);
        FavoriteButton.Content = detail.IsFavorite
            ? FamilyStudioText.Get("UnfavoriteLabel")
            : FamilyStudioText.Get("FavoriteLabel");
        UpdateTypeDetail();
    }

    private void ClearDetail(string message)
    {
        _selectedDetail = null;
        FamilyNameText.Text = message;
        StatusText.Text = string.Empty;
        CategoryText.Text = string.Empty;
        DisciplineText.Text = string.Empty;
        Types.ItemsSource = null;
        TypeParameters.ItemsSource = null;
        Tags.ItemsSource = null;
        InstanceParameters.ItemsSource = null;
        Thumbnail.Source = null;
        PreviewPlaceholder.Visibility = Visibility.Visible;
        PathText.Text = string.Empty;
        ModifiedText.Text = string.Empty;
        CatalogCheckText.Text = string.Empty;
        FavoriteButton.Content = FamilyStudioText.Get("FavoriteLabel");
    }

    private void UpdateTypeDetail()
    {
        if (_selectedDetail is null)
        {
            return;
        }

        if (Types.SelectedItem is FamilyTypeDetail type)
        {
            TypeParameters.ItemsSource = type.Parameters;
            Thumbnail.Source = LoadThumbnail(type.ThumbnailPath ?? _selectedDetail.Summary.ThumbnailPath);
        }
        else
        {
            TypeParameters.ItemsSource = null;
            Thumbnail.Source = LoadThumbnail(_selectedDetail.Summary.ThumbnailPath);
        }

        PreviewPlaceholder.Visibility = Thumbnail.Source is null ? Visibility.Visible : Visibility.Collapsed;
    }

    private static BitmapSource? LoadThumbnail(string? path)
    {
        if (string.IsNullOrWhiteSpace(path) || !File.Exists(path))
        {
            return null;
        }

        BitmapImage image = new BitmapImage();
        image.BeginInit();
        image.CacheOption = BitmapCacheOption.OnLoad;
        image.UriSource = new Uri(path, UriKind.Absolute);
        image.EndInit();
        image.Freeze();
        return image;
    }

    private void RunSelected(bool shouldPlace)
    {
        FamilySearchResult? family = GetSelectedFamily();
        if (family is null)
        {
            ShowWarning(FamilyStudioText.Get("SelectFamilyFirstLabel"));
            return;
        }

        try
        {
            if (shouldPlace)
            {
                PlacementFamily = family;
                DialogResult = true;
                return;
            }

            _loadService.Load(family);
            _repository.RecordUse(family.Id, FamilyUseAction.Loaded, DateTimeOffset.UtcNow);
            UpdateDetail();
        }
        catch (Exception exception)
        {
            ShowWarning(exception.Message);
        }
    }

    private void ToggleFavorite()
    {
        FamilySearchResult? selected = GetSelectedFamily();
        if (selected is null)
        {
            return;
        }

        FamilyDetail? detail = _repository.GetDetail(selected.Id);
        if (detail is not null)
        {
            _repository.SetFavorite(selected.Id, !detail.IsFavorite);
            UpdateDetail();
        }
    }

    private void CopyPath()
    {
        FamilySearchResult? selected = GetSelectedFamily();
        if (selected is not null)
        {
            Clipboard.SetText(selected.FilePath);
        }
    }

    private void OpenFolder()
    {
        FamilySearchResult? selected = GetSelectedFamily();
        if (selected is not null && File.Exists(selected.FilePath))
        {
            Process.Start(new ProcessStartInfo("explorer.exe", "/select,\"" + selected.FilePath + "\"") { UseShellExecute = true });
        }
    }

    private void RefreshIndex()
    {
        if (_refreshIndex is null)
        {
            ShowWarning(FamilyStudioText.Get("RefreshUnavailableLabel"));
            return;
        }

        try
        {
            IndexRunSummary? summary = _refreshIndex();
            if (summary is null)
            {
                return;
            }

            string message = string.Format(
                FamilyStudioText.Get("RefreshSummaryFormat"),
                summary.FilesSeen,
                summary.FilesUpdated,
                summary.FilesSkipped,
                summary.FilesFailed);
            if (summary.FilesFailed > 0)
            {
                message += "\n\n" + BuildRefreshDetails(summary);
            }

            if (summary.FilesFailed > 0)
            {
                ShowWarning(message);
            }
            else
            {
                KlaAlertWindow.ShowInformation(this, FamilyStudioText.Get("FamilyStudioTitle"), FamilyStudioText.Get("RefreshCompleteLabel"), message);
            }
            LoadFilterOptions();
            Search();
        }
        catch (Exception exception)
        {
            ShowWarning(exception.Message);
        }
    }

    private static string BuildRefreshDetails(IndexRunSummary summary)
    {
        return FamilyStudioText.Get("RefreshIssuesLabel") + "\n" + string.Join(
            "\n\n",
            summary.Errors.Take(8).Select(error => Path.GetFileName(error.FilePath) + ":\n" + error.Message));
    }

    private void ShowWarning(string message)
    {
        KlaAlertWindow.ShowWarning(
            this,
            FamilyStudioText.Get("FamilyStudioTitle"),
            FamilyStudioText.Get("FamilyStudioAttentionLabel"),
            message);
    }

    private sealed class FamilyResultItem : INotifyPropertyChanged
    {
        private bool _isChecked;

        internal FamilyResultItem(FamilySearchResult family)
        {
            Family = family;
        }

        internal FamilySearchResult Family { get; }
        public long Id => Family.Id;
        public string Name => Family.FamilyName;
        public string Category => Family.Category ?? FamilyStudioText.Get("UnavailableValue");
        public string Subtitle => Category + (string.IsNullOrWhiteSpace(Family.Discipline) ? string.Empty : " · " + Family.Discipline);
        public string? ThumbnailPath => Family.ThumbnailPath;
        public bool IsChecked
        {
            get => _isChecked;
            set
            {
                if (_isChecked == value) return;
                _isChecked = value;
                PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(IsChecked)));
            }
        }
        public string FlagText => Family.HasExactDuplicates
            ? Family.ExactDuplicateCount.ToString(CultureInfo.InvariantCulture)
            : Family.HasNameVariants
                ? Family.NameVariantCount.ToString(CultureInfo.InvariantCulture)
                : string.Empty;
        public Visibility FlagVisibility => Family.HasExactDuplicates || Family.HasNameVariants
            ? Visibility.Visible
            : Visibility.Collapsed;

        public event PropertyChangedEventHandler? PropertyChanged;
    }
}
