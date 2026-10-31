using System.Globalization;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Media;

namespace KLCode.Wpf.Views;

public enum KlaAlertKind
{
    Information,
    Warning,
    Blocking,
}

public partial class KlaAlertWindow : Window
{
    public KlaAlertWindow(string title, string message)
        : this(title, title, message, KlaAlertKind.Information)
    {
    }

    public KlaAlertWindow(string title, string heading, string message, KlaAlertKind kind, string? version = null)
    {
        ThemeBootstrapper.Apply(Resources, CultureInfo.CurrentUICulture.Name);
        InitializeComponent();
        WindowChrome.Attach(this, window_shell, title, version);
        AlertHeading.Text = heading ?? string.Empty;
        AlertMessage.Text = message ?? string.Empty;

        string resourceKey;
        switch (kind)
        {
            case KlaAlertKind.Warning:
                resourceKey = "KlaWarningBrush";
                AlertIcon.Content = FindResource("kliconWarnAlert");
                break;
            case KlaAlertKind.Blocking:
                resourceKey = "KlaBlockingBrush";
                AlertIcon.Content = FindResource("kliconErrorAlert");
                break;
            default:
                resourceKey = "KlaInfoBrush";
                AlertIcon.Content = FindResource("kliconInfoAlert");
                break;
        }

        Brush accent = (Brush)FindResource(resourceKey);
        AlertIconBorder.BorderBrush = accent;
        AlertIcon.Foreground = accent;
        AutomationProperties.SetName(AlertIcon, kind.ToString());
    }

    public static void Show(Window? owner, string title, string message)
    {
        Show(owner, title, title, message, KlaAlertKind.Information);
    }

    public static void ShowInformation(Window? owner, string title, string heading, string message)
    {
        Show(owner, title, heading, message, KlaAlertKind.Information);
    }

    public static void ShowWarning(Window? owner, string title, string heading, string message)
    {
        Show(owner, title, heading, message, KlaAlertKind.Warning);
    }

    public static void ShowBlocking(Window? owner, string title, string heading, string message)
    {
        Show(owner, title, heading, message, KlaAlertKind.Blocking);
    }

    private static void Show(Window? owner, string title, string heading, string message, KlaAlertKind kind)
    {
        string? version = (owner?.Content as System.Windows.Controls.ContentControl)?.Tag
            is WindowChromeMetadata caller ? caller.VersionText : null;
        KlaAlertWindow window = new KlaAlertWindow(title, heading, message, kind, version);
        if (owner is not null)
        {
            window.Owner = owner;
        }

        window.ShowDialog();
    }

    private void OnCloseClick(object sender, RoutedEventArgs e)
    {
        Close();
    }
}
