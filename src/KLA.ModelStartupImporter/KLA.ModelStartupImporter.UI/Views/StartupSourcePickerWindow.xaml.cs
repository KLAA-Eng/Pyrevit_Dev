using System;
using System.Globalization;
using System.IO;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using KLA.ModelStartupImporter.Core;
using KLA.ModelStartupImporter.UI.ViewModels;
using KLCode.Wpf;
using Microsoft.Win32;

namespace KLA.ModelStartupImporter.UI.Views;

public partial class StartupSourcePickerWindow : Window
{
    private readonly StartupSourcePickerViewModel _viewModel = new StartupSourcePickerViewModel();

    public StartupSourcePickerWindow()
        : this(string.Empty)
    {
    }

    public StartupSourcePickerWindow(string destinationProject)
    {
        ThemeBootstrapper.Apply(Resources, CultureInfo.CurrentUICulture.Name);
        StartupImporterText.ApplyToolStrings(Resources);
        InitializeComponent();
        _viewModel.DestinationProject = string.IsNullOrWhiteSpace(destinationProject)
            ? StartupImporterText.Get("UnknownDestinationLabel")
            : destinationProject;
        _viewModel.ChecklistStatus = StartupImporterText.Get("ChooseChecklistStatusLabel");
        _viewModel.SettingsStatus = StartupImporterText.Get("ChooseSettingsStatusLabel");
        DataContext = _viewModel;
        ApplyValidationColors();
    }

    public string ChecklistPath => _viewModel.ChecklistPath;
    public string SettingsPath => _viewModel.SettingsPath;
    public StartupDocumentModel? ValidatedDocument { get; private set; }
    public StartupImportSettings? ValidatedSettings { get; private set; }

    private void OnBrowseChecklistClick(object sender, RoutedEventArgs e)
    {
        OpenFileDialog dialog = new OpenFileDialog
        {
            Title = StartupImporterText.Get("BrowseChecklistLabel"),
            Filter = StartupImporterText.Get("ChecklistFileFilter"),
            CheckFileExists = true,
            Multiselect = false,
        };
        if (dialog.ShowDialog(this) == true)
        {
            _viewModel.ChecklistPath = dialog.FileName;
            ValidateChecklist();
        }
    }

    private void OnBrowseSettingsClick(object sender, RoutedEventArgs e)
    {
        OpenFileDialog dialog = new OpenFileDialog
        {
            Title = StartupImporterText.Get("BrowseSettingsLabel"),
            Filter = StartupImporterText.Get("SettingsFileFilter"),
            CheckFileExists = true,
            Multiselect = false,
        };
        if (dialog.ShowDialog(this) == true)
        {
            _viewModel.SettingsPath = dialog.FileName;
            ValidateSettings();
        }
    }

    private void ValidateChecklist()
    {
        try
        {
            ValidatedDocument = new StartupDocumentReader().Read(_viewModel.ChecklistPath);
            _viewModel.IsChecklistValid = true;
            _viewModel.ChecklistStatus = string.Format(
                StartupImporterText.Get("ChecklistValidFormat"),
                ValidatedDocument.Items.Count,
                ShortHash(ValidatedDocument.FileHash));
        }
        catch (Exception exception)
        {
            ValidatedDocument = null;
            _viewModel.IsChecklistValid = false;
            _viewModel.ChecklistStatus = string.Format(StartupImporterText.Get("ValidationFailedFormat"), exception.Message);
        }
        ApplyValidationColors();
    }

    private void ValidateSettings()
    {
        try
        {
            ValidatedSettings = new JsonStartupSettingsProvider().Load(_viewModel.SettingsPath);
            _viewModel.AreSettingsValid = true;
            _viewModel.SettingsStatus = StartupImporterText.Get("SettingsValidLabel");
            _viewModel.SeedModelStatus = string.Format(
                StartupImporterText.Get("SeedModelFormat"),
                ValidatedSettings.SeedModelPath,
                File.Exists(ValidatedSettings.SeedModelPath)
                    ? StartupImporterText.Get("ReachableLabel")
                    : StartupImporterText.Get("UnavailableLabel"));
            _viewModel.CatalogStatus = string.Format(
                StartupImporterText.Get("CatalogVersionFormat"),
                ValidatedSettings.CatalogVersion);
        }
        catch (Exception exception)
        {
            ValidatedSettings = null;
            _viewModel.AreSettingsValid = false;
            _viewModel.SettingsStatus = string.Format(StartupImporterText.Get("ValidationFailedFormat"), exception.Message);
            _viewModel.SeedModelStatus = string.Empty;
            _viewModel.CatalogStatus = string.Empty;
        }
        ApplyValidationColors();
    }

    private void ApplyValidationColors()
    {
        ChecklistStatus.Foreground = (Brush)FindResource(_viewModel.IsChecklistValid ? "KlaInfoBrush" : "KlaMutedTextBrush");
        SettingsStatus.Foreground = (Brush)FindResource(_viewModel.AreSettingsValid ? "KlaInfoBrush" : "KlaMutedTextBrush");
    }

    private static string ShortHash(string hash)
    {
        return hash.Length <= 8 ? hash : hash.Substring(0, 4) + "…" + hash.Substring(hash.Length - 2, 2);
    }

    private void OnReviewClick(object sender, RoutedEventArgs e)
    {
        if (_viewModel.CanReview)
        {
            DialogResult = true;
        }
    }

    private void OnCancelClick(object sender, RoutedEventArgs e) => DialogResult = false;

    private void OnHeaderMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.LeftButton == MouseButtonState.Pressed) DragMove();
    }
}
