using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace KLA.ModelStartupImporter.UI.ViewModels;

public sealed class StartupSourcePickerViewModel : INotifyPropertyChanged
{
    private string _checklistPath = string.Empty;
    private string _settingsPath = string.Empty;
    private string _checklistStatus = string.Empty;
    private string _settingsStatus = string.Empty;
    private string _seedModelStatus = string.Empty;
    private string _catalogStatus = string.Empty;
    private string _destinationProject = string.Empty;
    private bool _isChecklistValid;
    private bool _areSettingsValid;

    public event PropertyChangedEventHandler? PropertyChanged;

    public string ChecklistPath { get => _checklistPath; set => Set(ref _checklistPath, value); }
    public string SettingsPath { get => _settingsPath; set => Set(ref _settingsPath, value); }
    public string ChecklistStatus { get => _checklistStatus; set => Set(ref _checklistStatus, value); }
    public string SettingsStatus { get => _settingsStatus; set => Set(ref _settingsStatus, value); }
    public string SeedModelStatus { get => _seedModelStatus; set => Set(ref _seedModelStatus, value); }
    public string CatalogStatus { get => _catalogStatus; set => Set(ref _catalogStatus, value); }
    public string DestinationProject { get => _destinationProject; set => Set(ref _destinationProject, value); }

    public bool IsChecklistValid
    {
        get => _isChecklistValid;
        set
        {
            if (_isChecklistValid == value) return;
            _isChecklistValid = value;
            Notify();
            Notify(nameof(CanReview));
        }
    }

    public bool AreSettingsValid
    {
        get => _areSettingsValid;
        set
        {
            if (_areSettingsValid == value) return;
            _areSettingsValid = value;
            Notify();
            Notify(nameof(CanReview));
        }
    }

    public bool CanReview => IsChecklistValid && AreSettingsValid;

    private void Set(ref string field, string? value, [CallerMemberName] string? propertyName = null)
    {
        string normalized = value?.Trim() ?? string.Empty;
        if (field == normalized) return;
        field = normalized;
        Notify(propertyName);
    }

    private void Notify([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
