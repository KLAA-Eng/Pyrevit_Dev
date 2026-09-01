using System.Windows;
using System.Windows.Input;

namespace KLCode.Wpf.Views;

public partial class DesignSystemSmokeWindow : Window
{
    public DesignSystemSmokeWindow()
        : this(SupportedLocaleCatalog.FallbackLocale)
    {
    }

    public DesignSystemSmokeWindow(string? locale)
    {
        ThemeBootstrapper.Apply(Resources, locale);
        InitializeComponent();
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
