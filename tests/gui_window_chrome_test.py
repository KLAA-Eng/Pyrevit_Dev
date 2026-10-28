"""Exercise shared event/lifecycle boundaries; real WPF templates run in the probe."""
import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib'))
from GUI.window_chrome import load_window, fit_window_height


class Event:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def emit(self, sender, args):
        for handler in self.handlers:
            handler(sender, args)


class Parts:
    def __init__(self):
        self.Click = Event()
        self.MouseLeftButtonDown = Event()
        self.RequestNavigate = Event()


class Merged(list):
    def Add(self, value):
        self.append(value)


class Resources:
    def __init__(self):
        self.MergedDictionaries = Merged()


class Shell:
    def __init__(self):
        self.parts = {name: Parts() for name in (
            'Header', 'Title', 'Close', 'Body', 'Footer', 'Version', 'Prototype', 'Outreach')}
        self.Template = types.SimpleNamespace(FindName=lambda name, shell: self.parts[name[5:]])

    def ApplyTemplate(self):
        self.applied = True


class Window:
    def __init__(self):
        self.Resources = Resources()
        self.DataContext = object()
        self.window_shell = Shell()
        self.closed = False
        self.drags = 0

    def Close(self):
        self.closed = True

    def DragMove(self):
        self.drags += 1


def module(**attributes):
    result = types.ModuleType('boundary')
    result.__dict__.update(attributes)
    return result


class WindowChromeTests(unittest.TestCase):
    def setUp(self):
        self.loads = []
        self.destinations = []
        self.window = Window()
        self.host = {
            'wpf': module(LoadComponent=lambda owner, path: self.loads.append((owner, path))),
            'System': module(Uri=lambda path: path),
            'System.Windows': module(ResourceDictionary=Resources),
            'System.Windows.Input': module(MouseButtonState=module(Pressed='pressed')),
            'System.Diagnostics.Process': module(Start=self.destinations.append),
        }

    def load(self, navigate=None):
        with patch.dict(sys.modules, self.host):
            return load_window(self.window, 'body.xaml', 'Caller', 'v1.3', navigate)

    def test_loading_preserves_workflow_data_and_existing_resources(self):
        existing = object()
        self.window.Resources.MergedDictionaries.Add(existing)
        context = self.window.DataContext
        chrome = self.load()
        self.assertIs(context, self.window.DataContext)
        self.assertIs(existing, self.window.Resources.MergedDictionaries[0])
        self.assertEqual(2, len(self.window.Resources.MergedDictionaries))
        self.assertEqual([(self.window, 'body.xaml')], self.loads)
        self.assertEqual('v1.3', chrome.shell.Tag.VersionText)
        self.assertIs(chrome, self.window._kla_chrome)
        self.assertFalse(self.window.closed)

    def test_close_is_owned_by_the_shell_without_exiting_the_host(self):
        chrome = self.load()
        chrome.close_button.Click.emit(None, None)
        self.assertTrue(self.window.closed)

    def test_content_height_uses_current_width_and_clamps_to_caller_limits(self):
        measurements = []
        content = types.SimpleNamespace(Measure=measurements.append,
                                        DesiredSize=types.SimpleNamespace(Height=0))
        window = types.SimpleNamespace(Content=content, Width=560, MinHeight=240, MaxHeight=640)
        host = {'System.Windows': module(Size=lambda width, height: (width, height))}
        with patch.dict(sys.modules, host):
            for natural, expected in ((100, 240), (300.2, 301), (2000, 640)):
                content.DesiredSize.Height = natural
                self.assertEqual(expected, fit_window_height(window))
                self.assertEqual(expected, window.Height)
        self.assertEqual([(560, float('inf'))] * 3, measurements)

    def test_only_a_pressed_left_button_starts_dragging(self):
        chrome = self.load()
        with patch.dict(sys.modules, self.host):
            for button in ('released', 'pressed'):
                args = types.SimpleNamespace(LeftButton=button, Handled=False)
                chrome.header.MouseLeftButtonDown.emit(None, args)
                self.assertEqual(button == 'pressed', args.Handled)
        self.assertEqual(1, self.window.drags)

    def test_gallery_callback_suppresses_system_navigation(self):
        simulated = []
        chrome = self.load(simulated.append)
        args = types.SimpleNamespace(Uri=types.SimpleNamespace(AbsoluteUri='https://example.test'), Handled=False)
        chrome.prototype.RequestNavigate.emit(None, args)
        self.assertEqual(['https://example.test'], simulated)
        self.assertEqual([], self.destinations)
        self.assertTrue(args.Handled)

    def test_ordinary_footer_click_opens_the_shared_destination_once(self):
        chrome = self.load()
        uri = chrome.shell.Tag.OutreachUri
        args = types.SimpleNamespace(Uri=types.SimpleNamespace(AbsoluteUri=uri), Handled=False)
        with patch.dict(sys.modules, self.host):
            chrome.outreach.RequestNavigate.emit(None, args)
        self.assertEqual([uri], self.destinations)
        self.assertTrue(args.Handled)


if __name__ == '__main__':
    unittest.main()
