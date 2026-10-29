using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using KLA.ModelStartupImporter.Core;
using KLA.ModelStartupImporter.UI.Views;
using KLCode.Wpf;
using KLCode.Wpf.Views;
using KLCode.FamilyStudio.Revit.Views;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        Application application = new Application { ShutdownMode = ShutdownMode.OnExplicitShutdown };
        try
        {
            string? output = args.Length == 0 ? null : args[0];
            if (output is not null) Directory.CreateDirectory(output);
            CatalogItem catalogItem = new CatalogItem("D-001", "Fictional Source", "Fictional Target",
                StartupItemCategory.Detail, Array.Empty<string>(), Array.Empty<string>());
            ContentCatalog catalog = new ContentCatalog(new[] { catalogItem });
            StartupImportSettings settings = new StartupImportSettings("fictional.rvt", "sample", catalog);
            StartupItem item = new StartupItem("D-001", "Fictional Detail", StartupItemCategory.Detail,
                true, string.Empty, "sample row 2", string.Empty);
            StartupDocumentModel document = new StartupDocumentModel("fictional.xlsx", StartupSourceType.Excel,
                DateTime.UtcNow, new string('A', 64), new[] { item });
            StartupImportReview review = new StartupImportReviewBuilder().Build(document, catalog, Array.Empty<string>());
            Check(new StartupSourcePickerWindow("Fictional Destination"), "source-picker", "v0.0", output);
            Check(new StartupImportReviewWindow(document, settings, review), "import-review", "v0.0", output);
            Check(new BlockingIssuesWindow(settings, review), "blocking-issues", "v0.0", output);
            foreach (KlaAlertKind kind in new[] { KlaAlertKind.Information, KlaAlertKind.Warning, KlaAlertKind.Blocking })
            {
                Check(new KlaAlertWindow("Fictional Alert", kind.ToString(),
                    string.Join("\n", Enumerable.Repeat("Long fictional message; no model operation runs.", 40)), kind),
                    "alert-" + kind, string.Empty, output);
            }

            Check(new FamilyStudioWindow(new EmptyFamilyRepository(), new ForbiddenFamilyLoadService(), null),
                "family-studio", "v0.0", output);
            Console.WriteLine("Compiled WPF: seven actual window instances across all five classes passed. Family Studio uses its real UI and ports with an in-memory empty repository. No window shown; no model, database, import, picker or navigation actions run.");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error);
            return 1;
        }
        finally { application.Shutdown(); }
    }

    private static void Check(Window window, string identity, string version, string? output)
    {
        ContentControl shell = (ContentControl)window.Content;
        shell.Measure(new Size(window.Width, window.Height));
        shell.Arrange(new Rect(0, 0, window.Width, window.Height));
        shell.UpdateLayout();
        DispatcherFrame frame = new DispatcherFrame();
        Dispatcher.CurrentDispatcher.BeginInvoke(DispatcherPriority.Background, new Action(() => frame.Continue = false));
        Dispatcher.PushFrame(frame);
        TextBlock footer = (TextBlock)shell.Template.FindName("PART_Version", shell);
        FrameworkElement header = (FrameworkElement)shell.Template.FindName("PART_Header", shell);
        FrameworkElement footerGrid = (FrameworkElement)shell.Template.FindName("PART_Footer", shell);
        Require(footer.Text == version, identity + " caller version");
        double chromeRow = ((GridLength)window.FindResource("KlaChromeRow")).Value;
        Require(header.ActualHeight == chromeRow && footerGrid.ActualHeight == chromeRow, identity + " chrome heights");
        Require(window.FindResource("KlaIconSearch") is DrawingImage, identity + " canonical vector search");
        Border infoChip = new Border { Style = (Style)window.FindResource("KlaInfoChipStyle") };
        Require(((SolidColorBrush)infoChip.BorderBrush).Color ==
            ((SolidColorBrush)window.FindResource("KlaInfoBrush")).Color,
            identity + " information-chip accent");
        if (identity == "family-studio")
        {
            Require(HasCollapsedAncestor((Border)window.FindName("StatusChip")),
                "Empty detail status must not leave an empty chip border.");
            foreach (string group in new[] { "ContentMode", "SearchScope", "ViewMode" })
            {
                RadioButton[] choices = Descendants(shell).OfType<RadioButton>()
                    .Where(radio => radio.GroupName == group).ToArray();
                FrameworkElement parent = (FrameworkElement)choices[0].Parent;
                double first = choices[0].TranslatePoint(new Point(0, 0), parent).X;
                double second = choices[1].TranslatePoint(new Point(0, 0), parent).X;
                Require(Math.Abs(second - first - choices[0].ActualWidth - ((Thickness)window.FindResource("KlaPairGap")).Right) < 0.1,
                    group + " related-choice gap");
            }
            Button favorite = (Button)window.FindName("FavoriteButton");
            favorite.Content = "Unfavorite";
            shell.UpdateLayout();
            Require(Descendants(favorite).OfType<ContentControl>().Any(icon => icon.Content is Geometry),
                "Favorite state caption changes must preserve the canonical icon.");
            favorite.Content = "Favorite";
            shell.UpdateLayout();
        }
        foreach (Button button in Descendants(shell).OfType<Button>().Where(button => button.Content is string))
        {
            if (HasCollapsedAncestor(button)) continue;
            if ((string)button.Content == "Close") continue;
            double buttonWidth = (double)window.FindResource("KlaButtonWidth"), mainWidth = (double)window.FindResource("KlaMainButtonWidth");
            double compactHeight = (double)window.FindResource("KlaCompactHeight"), controlHeight = (double)window.FindResource("KlaControlHeight");
            Require(button.ActualWidth == buttonWidth || button.ActualWidth == mainWidth,
                identity + " button width: " + button.Content + " = " + button.ActualWidth);
            Require(button.ActualHeight == compactHeight || button.ActualHeight == controlHeight,
                identity + " button height: " + button.Content + " = " + button.ActualHeight);
        }
        if (output is not null)
        {
            RenderTargetBitmap bitmap = new RenderTargetBitmap((int)window.Width, (int)window.Height, 96, 96, PixelFormats.Pbgra32);
            bitmap.Render(shell);
            PngBitmapEncoder encoder = new PngBitmapEncoder();
            encoder.Frames.Add(BitmapFrame.Create(bitmap));
            using (Stream stream = File.Create(Path.Combine(output, identity + ".png"))) encoder.Save(stream);
        }
        Console.WriteLine(identity + ": shared resources, chrome and action dimensions passed.");
        window.Close();
    }

    private static IEnumerable<DependencyObject> Descendants(DependencyObject parent)
    {
        for (int index = 0; index < VisualTreeHelper.GetChildrenCount(parent); index++)
        {
            DependencyObject child = VisualTreeHelper.GetChild(parent, index);
            yield return child;
            foreach (DependencyObject nested in Descendants(child)) yield return nested;
        }
    }

    private static bool HasCollapsedAncestor(DependencyObject control)
    {
        for (DependencyObject? current = control; current is not null; current = VisualTreeHelper.GetParent(current))
            if (current is UIElement element && element.Visibility == Visibility.Collapsed) return true;
        return false;
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

}
