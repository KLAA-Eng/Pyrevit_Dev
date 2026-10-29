using System.Globalization;
using System.Windows;
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
        WindowChrome.Attach(this, window_shell, Title, StartupImporterText.Get("ToolVersion"));
        _viewModel = new BlockingIssuesViewModel(settings, review);
        DataContext = _viewModel;
    }

    private void OnCopyIssueReportClick(object sender, RoutedEventArgs e) => Clipboard.SetText(_viewModel.BuildReport());
    private void OnCloseClick(object sender, RoutedEventArgs e) => Close();
}
