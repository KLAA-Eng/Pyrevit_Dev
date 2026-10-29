using System;
using System.Diagnostics;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Navigation;

namespace KLCode.Wpf;

/// <summary>Bind the same shell parts as the Python adapter without owning workflow lifetime.</summary>
public sealed class WindowChrome
{
    private readonly Window _window;
    private readonly Action _close;

    private WindowChrome(Window window, ContentControl shell, string? title, string? version, Action? close)
    {
        _window = window;
        _close = close ?? window.Close;
        shell.Tag = new WindowChromeMetadata(title, version);
        window.Title = ((WindowChromeMetadata)shell.Tag).Title;
        shell.ApplyTemplate();
        Part<Button>(shell, "PART_Close").Click += OnClose;
        window.PreviewKeyDown += OnKey;
        Part<Grid>(shell, "PART_Header").MouseLeftButtonDown += OnDrag;
        Hyperlink prototype = Part<Hyperlink>(shell, "PART_Prototype");
        Hyperlink outreach = Part<Hyperlink>(shell, "PART_Outreach");
        prototype.RequestNavigate += OnNavigate;
        outreach.RequestNavigate += OnNavigate;
        // Labels and destinations come from KLCodeChrome.xaml through the template (DynamicResource), so the
        // locale dictionary ThemeBootstrapper merges after the controls overrides them without adapter code.
    }

    public static WindowChrome Attach(Window window, ContentControl shell, string? title,
        string? version = null, Action? close = null)
    {
        if (window is null) throw new ArgumentNullException(nameof(window));
        if (shell is null) throw new ArgumentNullException(nameof(shell));
        return new WindowChrome(window, shell, title, version, close);
    }

    private static T Part<T>(ContentControl shell, string name) where T : class =>
        shell.Template.FindName(name, shell) as T
        ?? throw new InvalidOperationException("The shared window shell is missing " + name + ".");

    private void OnClose(object sender, RoutedEventArgs args) => _close();

    /// <summary>Escape follows the same close policy as the header Close button.</summary>
    private void OnKey(object sender, KeyEventArgs args)
    {
        if (args.Key == Key.Escape)
        {
            args.Handled = true;
            _close();
        }
    }

    private void OnDrag(object sender, MouseButtonEventArgs args)
    {
        if (args.LeftButton == MouseButtonState.Pressed)
        {
            _window.DragMove();
            args.Handled = true;
        }
    }

    private static void OnNavigate(object sender, RequestNavigateEventArgs args)
    {
        args.Handled = true;
        Process.Start(new ProcessStartInfo(args.Uri.AbsoluteUri) { UseShellExecute = true });
    }
}
