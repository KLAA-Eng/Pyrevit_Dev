using System.Globalization;
using System.Windows;
using System.Windows.Input;
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

    public KlaAlertWindow(string title, string heading, string message, KlaAlertKind kind)
    {
        ThemeBootstrapper.Apply(Resources, CultureInfo.CurrentUICulture.Name);
        InitializeComponent();
        Title = title ?? string.Empty;
        AlertTitle.Text = Title;
        AlertHeading.Text = heading ?? string.Empty;
        AlertMessage.Text = message ?? string.Empty;

        string resourceKey;
        switch (kind)
        {
            case KlaAlertKind.Warning:
                resourceKey = "KlaWarningBrush";
                AlertIcon.Text = "!";
                break;
            case KlaAlertKind.Blocking:
                resourceKey = "KlaBlockingBrush";
                AlertIcon.Text = "!";
                break;
            default:
                resourceKey = "KlaInfoBrush";
                AlertIcon.Text = "i";
                AlertIcon.FontFamily = new FontFamily("Georgia");
                AlertIcon.FontStyle = FontStyles.Italic;
                break;
        }

        Brush accent = (Brush)FindResource(resourceKey);
        AlertIconBorder.BorderBrush = accent;
        AlertIcon.Foreground = accent;
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
        KlaAlertWindow window = new KlaAlertWindow(title, heading, message, kind);
        if (owner is not null)
        {
            window.Owner = owner;
        }

        window.ShowDialog();
    }

    private void OnHeaderMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.LeftButton == MouseButtonState.Pressed)
        {
            DragMove();
        }
    }

    private void OnCloseClick(object sender, RoutedEventArgs e)
    {
        Close();
    }
}
