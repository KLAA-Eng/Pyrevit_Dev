using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Imaging;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Core.Models;
using KLCode.FamilyStudio.Core.Repositories;
using KLCode.FamilyStudio.Core.Search;
using KLCode.FamilyStudio.Revit.Services;

namespace KLCode.FamilyStudio.Revit.Views;

internal sealed class FamilyStudioWindow : Window
{
    private readonly IFamilyRepository _repository;
    private readonly IFamilyLoadService _loadService;
    private readonly Func<IndexRunSummary?>? _refreshIndex;
    private readonly TextBox _searchBox = new TextBox { MinWidth = 300, Margin = new Thickness(4) };
    private readonly ListBox _results = new ListBox { MinHeight = 300, Margin = new Thickness(4), DisplayMemberPath = nameof(FamilySearchResult.FamilyName) };
    private readonly Image _thumbnail = new Image { Width = 260, Height = 180, Margin = new Thickness(4), Stretch = System.Windows.Media.Stretch.Uniform };
    private readonly ComboBox _types = new ComboBox { Margin = new Thickness(4), DisplayMemberPath = nameof(FamilyTypeDetail.Name) };
    private readonly TextBlock _detail = new TextBlock { Margin = new Thickness(4), TextWrapping = TextWrapping.Wrap };
    private FamilyDetail? _selectedDetail;

    internal FamilySearchResult? PlacementFamily { get; private set; }

    internal FamilyStudioWindow(
        IFamilyRepository repository,
        IFamilyLoadService loadService,
        Func<IndexRunSummary?>? refreshIndex)
    {
        _repository = repository ?? throw new ArgumentNullException(nameof(repository));
        _loadService = loadService ?? throw new ArgumentNullException(nameof(loadService));
        _refreshIndex = refreshIndex;
        Title = "KLCode Family Studio";
        Width = 980;
        Height = 640;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        Content = BuildContent();
        Search();
    }

    private UIElement BuildContent()
    {
        DockPanel root = new DockPanel();
        StackPanel searchRow = new StackPanel { Orientation = Orientation.Horizontal };
        searchRow.Children.Add(_searchBox);
        searchRow.Children.Add(CreateButton("Search", (_, _) => Search()));
        searchRow.Children.Add(CreateButton("Favorites", (_, _) => ShowFavorites()));
        searchRow.Children.Add(CreateButton("Recent", (_, _) => ShowRecent()));
        searchRow.Children.Add(CreateButton("Refresh Library", (_, _) => RefreshIndex()));
        DockPanel.SetDock(searchRow, Dock.Top);
        root.Children.Add(searchRow);

        StackPanel actions = new StackPanel { Orientation = Orientation.Horizontal };
        actions.Children.Add(CreateButton("Load", (_, _) => RunSelected(false)));
        actions.Children.Add(CreateButton("Load && Place", (_, _) => RunSelected(true)));
        actions.Children.Add(CreateButton("Favorite", (_, _) => ToggleFavorite()));
        actions.Children.Add(CreateButton("Copy Path", (_, _) => CopyPath()));
        actions.Children.Add(CreateButton("Open Folder", (_, _) => OpenFolder()));
        DockPanel.SetDock(actions, Dock.Bottom);
        root.Children.Add(actions);

        Grid content = new Grid();
        content.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        content.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(360) });
        _results.SelectionChanged += (_, _) => UpdateDetail();
        Grid.SetColumn(_results, 0);
        content.Children.Add(_results);

        StackPanel detailPanel = new StackPanel { Margin = new Thickness(4) };
        detailPanel.Children.Add(_thumbnail);
        detailPanel.Children.Add(new TextBlock { Text = "Type", Margin = new Thickness(4, 8, 4, 0) });
        _types.SelectionChanged += (_, _) => UpdateTypeDetail();
        detailPanel.Children.Add(_types);
        detailPanel.Children.Add(_detail);
        ScrollViewer detailScroller = new ScrollViewer { Content = detailPanel, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
        Grid.SetColumn(detailScroller, 1);
        content.Children.Add(detailScroller);
        root.Children.Add(content);
        return root;
    }

    private Button CreateButton(string label, RoutedEventHandler handler)
    {
        Button button = new Button { Content = label, Margin = new Thickness(4), MinWidth = 84 };
        button.Click += handler;
        return button;
    }

    private void Search()
    {
        SetResults(_repository.Search(new FamilySearchQuery(_searchBox.Text, null, null, null, 100)));
    }

    private void ShowFavorites()
    {
        SetResults(_repository.GetFavorites(100));
    }

    private void ShowRecent()
    {
        SetResults(_repository.GetRecent(100));
    }

    private void SetResults(IReadOnlyList<FamilySearchResult> families)
    {
        _results.ItemsSource = families;
        _results.SelectedIndex = families.Count > 0 ? 0 : -1;
        UpdateDetail();
    }

    private void UpdateDetail()
    {
        if (!(_results.SelectedItem is FamilySearchResult selected))
        {
            _selectedDetail = null;
            _types.ItemsSource = null;
            _thumbnail.Source = null;
            _detail.Text = "Select a family to view its details.";
            return;
        }

        FamilyDetail? detail = _repository.GetDetail(selected.Id);
        if (detail is null)
        {
            _selectedDetail = null;
            _types.ItemsSource = null;
            _thumbnail.Source = null;
            _detail.Text = "The selected family is no longer indexed.";
            return;
        }

        _selectedDetail = detail;
        _thumbnail.Source = LoadThumbnail(detail.Summary.ThumbnailPath);
        _types.ItemsSource = detail.Types;
        _types.SelectedIndex = detail.Types.Count > 0 ? 0 : -1;
        UpdateTypeDetail();
    }

    private void UpdateTypeDetail()
    {
        if (_selectedDetail is null)
        {
            return;
        }

        StringBuilder text = new StringBuilder();
        text.AppendLine(_selectedDetail.Summary.FamilyName);
        text.AppendLine("Category: " + (_selectedDetail.Summary.Category ?? "<unavailable>"));
        text.AppendLine("Status: " + (_selectedDetail.Summary.Status ?? "<unavailable>"));
        text.AppendLine("Discipline: " + (_selectedDetail.Summary.Discipline ?? "<unavailable>"));
        text.AppendLine("Favorite: " + (_selectedDetail.IsFavorite ? "Yes" : "No"));
        text.AppendLine("Path: " + _selectedDetail.Summary.FilePath);
        text.AppendLine("Tags: " + (_selectedDetail.Tags.Count == 0 ? "<none>" : string.Join(", ", _selectedDetail.Tags)));
        if (_types.SelectedItem is FamilyTypeDetail type)
        {
            text.AppendLine("Selected type: " + type.Name);
            text.AppendLine("Type parameters:");
            foreach (FamilyParameter parameter in type.Parameters)
            {
                text.AppendLine("- " + parameter.Name + ": " + (parameter.Value ?? "<no value>"));
            }
        }

        if (_selectedDetail.Parameters.Count > 0)
        {
            text.AppendLine("Instance parameter definitions:");
            foreach (FamilyParameter parameter in _selectedDetail.Parameters)
            {
                text.AppendLine("- " + parameter.Name + " (" + (parameter.StorageType ?? "unknown") + ")");
            }
        }

        _detail.Text = text.ToString();
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
        if (!(_results.SelectedItem is FamilySearchResult family))
        {
            MessageBox.Show(this, "Select a family first.", Title, MessageBoxButton.OK, MessageBoxImage.Information);
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
            MessageBox.Show(this, exception.Message, Title, MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void ToggleFavorite()
    {
        if (_results.SelectedItem is FamilySearchResult selected)
        {
            FamilyDetail? detail = _repository.GetDetail(selected.Id);
            if (detail is not null)
            {
                _repository.SetFavorite(selected.Id, !detail.IsFavorite);
                UpdateDetail();
            }
        }
    }

    private void CopyPath()
    {
        if (_results.SelectedItem is FamilySearchResult selected)
        {
            Clipboard.SetText(selected.FilePath);
        }
    }

    private void OpenFolder()
    {
        if (_results.SelectedItem is FamilySearchResult selected && File.Exists(selected.FilePath))
        {
            Process.Start(new ProcessStartInfo("explorer.exe", "/select,\"" + selected.FilePath + "\"") { UseShellExecute = true });
        }
    }

    private void RefreshIndex()
    {
        if (_refreshIndex is null)
        {
            MessageBox.Show(this, "Library refresh is not available in this Revit session.", Title, MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }

        try
        {
            IndexRunSummary? summary = _refreshIndex();
            if (summary is null)
            {
                return;
            }

            string message = "Seen: " + summary.FilesSeen + "; updated: " + summary.FilesUpdated + "; skipped: " + summary.FilesSkipped + "; preview/index issues: " + summary.FilesFailed;
            if (summary.FilesFailed > 0)
            {
                message += "\n\n" + BuildRefreshDetails(summary);
            }

            MessageBox.Show(
                this,
                message,
                Title,
                MessageBoxButton.OK,
                summary.FilesFailed == 0 ? MessageBoxImage.Information : MessageBoxImage.Warning);
            Search();
        }
        catch (Exception exception)
        {
            MessageBox.Show(this, exception.Message, Title, MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private static string BuildRefreshDetails(IndexRunSummary summary)
    {
        return "Issues:\n" + string.Join(
            "\n\n",
            summary.Errors.Take(8).Select(error =>
                Path.GetFileName(error.FilePath) + ":\n" + error.Message));
    }
}
