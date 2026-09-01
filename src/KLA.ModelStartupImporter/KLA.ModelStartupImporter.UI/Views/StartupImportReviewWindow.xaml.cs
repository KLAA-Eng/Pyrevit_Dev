using System;
using System.Globalization;
using System.Windows;
using System.Windows.Input;
using KLA.ModelStartupImporter.Core;
using KLA.ModelStartupImporter.UI.ViewModels;
using KLCode.Wpf;

namespace KLA.ModelStartupImporter.UI.Views;

public partial class StartupImportReviewWindow : Window
{
    private readonly StartupImportReviewViewModel _viewModel;

    public StartupImportReviewWindow(StartupDocumentModel document, StartupImportSettings settings, StartupImportReview review)
    {
        ThemeBootstrapper.Apply(Resources, CultureInfo.CurrentUICulture.Name);
        StartupImporterText.ApplyToolStrings(Resources);
        InitializeComponent();
        _viewModel = new StartupImportReviewViewModel(document, settings, review);
        DataContext = _viewModel;
    }

    public string[] SelectedItemIds => _viewModel.GetSelectedItemIds();
    private void OnSelectAllClick(object sender, RoutedEventArgs e) => _viewModel.SelectAll();
    private void OnSelectNoneClick(object sender, RoutedEventArgs e) => _viewModel.SelectNone();
    private void OnImportClick(object sender, RoutedEventArgs e) => DialogResult = true;
    private void OnCancelClick(object sender, RoutedEventArgs e) => DialogResult = false;
    private void OnHeaderMouseLeftButtonDown(object sender, MouseButtonEventArgs e) { if (e.LeftButton == MouseButtonState.Pressed) DragMove(); }
}
