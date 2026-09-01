using System.Globalization;
using System.Windows;
using System.Windows.Input;
using KLA.ModelStartupImporter.Core;
using KLA.ModelStartupImporter.UI.ViewModels;
using KLCode.Wpf;

namespace KLA.ModelStartupImporter.UI.Views;

public partial class BlockingIssuesWindow : Window
{
    private readonly BlockingIssuesViewModel _viewModel;

    public BlockingIssuesWindow(StartupImportSettings settings, StartupImportReview review)
    {
        ThemeBootstrapper.Apply(Resources, CultureInfo.CurrentUICulture.Name);
        StartupImporterText.ApplyToolStrings(Resources);
        InitializeComponent();
        _viewModel = new BlockingIssuesViewModel(settings, review);
        DataContext = _viewModel;
    }

    private void OnCopyIssueReportClick(object sender, RoutedEventArgs e) => Clipboard.SetText(_viewModel.BuildReport());
    private void OnCloseClick(object sender, RoutedEventArgs e) => Close();
    private void OnHeaderMouseLeftButtonDown(object sender, MouseButtonEventArgs e) { if (e.LeftButton == MouseButtonState.Pressed) DragMove(); }
}
