using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using KLCode.FamilyStudio.Core.Repositories;
using KLCode.FamilyStudio.Core.Search;
using KLCode.FamilyStudio.Revit.Services;

namespace KLCode.FamilyStudio.Revit.Views;

internal sealed class FamilyStudioWindow : Window
{
    private readonly IFamilyRepository _repository;
    private readonly IFamilyLoadService _loadService;
    private readonly TextBox _searchBox = new TextBox { MinWidth = 320, Margin = new Thickness(4) };
    private readonly ListBox _results = new ListBox { MinHeight = 300, Margin = new Thickness(4) };

    internal FamilySearchResult? PlacementFamily { get; private set; }

    public FamilyStudioWindow(IFamilyRepository repository, IFamilyLoadService loadService)
    {
        _repository = repository ?? throw new ArgumentNullException(nameof(repository));
        _loadService = loadService ?? throw new ArgumentNullException(nameof(loadService));
        Title = "KLCode Family Studio";
        Width = 720;
        Height = 520;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        Content = BuildContent();
        Search();
    }

    private UIElement BuildContent()
    {
        DockPanel root = new DockPanel();
        StackPanel searchRow = new StackPanel { Orientation = Orientation.Horizontal };
        Button searchButton = new Button { Content = "Search", Margin = new Thickness(4), IsDefault = true };
        searchButton.Click += (_, _) => Search();
        searchRow.Children.Add(_searchBox);
        searchRow.Children.Add(searchButton);
        DockPanel.SetDock(searchRow, Dock.Top);
        root.Children.Add(searchRow);

        StackPanel actions = new StackPanel { Orientation = Orientation.Horizontal };
        actions.Children.Add(CreateActionButton("Load", false));
        actions.Children.Add(CreateActionButton("Load && Place", true));
        DockPanel.SetDock(actions, Dock.Bottom);
        root.Children.Add(actions);
        _results.DisplayMemberPath = nameof(FamilySearchResult.FamilyName);
        root.Children.Add(_results);
        return root;
    }

    private Button CreateActionButton(string label, bool shouldPlace)
    {
        Button button = new Button { Content = label, Margin = new Thickness(4), MinWidth = 100 };
        button.Click += (_, _) => RunSelected(shouldPlace);
        return button;
    }

    private void Search()
    {
        IReadOnlyList<FamilySearchResult> families = _repository.Search(
            new FamilySearchQuery(_searchBox.Text, null, null, null, 100));
        _results.ItemsSource = families;
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
                // Revit's placement prompt must run after this modal window
                // closes. Otherwise Revit returns to the window after the user
                // finishes or cancels placement.
                PlacementFamily = family;
                DialogResult = true;
                return;
            }

            _loadService.Load(family);
        }
        catch (Exception exception)
        {
            MessageBox.Show(this, exception.Message, Title, MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }
}
