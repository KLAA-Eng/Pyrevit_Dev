"""Owned shown Command Switch pointer/capture contract; no input injection.

Called from the gallery fixture's opt-in shown checks. Outside dispatch uses
coordinates and a real routed event; native DragMove is not driven by synthetic
system input and remains a separate physical-host acceptance.
"""
import clr
clr.AddReference('WindowsBase')
clr.AddReference('PresentationCore')
from GUI.dialogs import create_command_switch, ActionChoice, CommandSwitch
from System import Action, Environment
from System.Windows import Window, Point
from System.Windows.Input import (Mouse, MouseButton, MouseButtonEventArgs,
                                  MouseButtonState, Key)
from System.Windows.Threading import DispatcherPriority, Dispatcher, DispatcherFrame
from System.Windows.Interop import ComponentDispatcher
from System.Windows.Controls import ContextMenu, MenuItem


def settle_pointer_layout(content):
    frame = DispatcherFrame()
    Dispatcher.CurrentDispatcher.BeginInvoke(DispatcherPriority.Background,
        Action(lambda: setattr(frame, 'Continue', False)))
    Dispatcher.PushFrame(frame)
    content.UpdateLayout()


class PointerArgs(object):
    Handled = False
    LeftButton = MouseButtonState.Pressed
    ChangedButton = MouseButton.Left

    def __init__(self, x, y):
        self.point = Point(x, y)

    def GetPosition(self, target):
        return self.point


def validate_command_switch_pointer():
    window = create_command_switch('Command pointer fixture', [ActionChoice('run', 'Run')],
                                   switches=[CommandSwitch('flag', 'Flag')])
    try:
        window.Show()
        window.Activate()
        settle_pointer_layout(window.Content)
        assert Mouse.Captured == window and window.IsMouseCaptureWithin
        window.pointer_down(window, PointerArgs(40, 40))
        window.pointer_move(window, PointerArgs(41, 41))
        assert not window._dragged and window.IsVisible
        button = window._command_buttons['run']
        assert Mouse.Capture(button)
        assert Mouse.Captured == button
        Mouse.Capture(None)
        settle_pointer_layout(window.Content)
        assert Mouse.Captured == window, 'Child releases must re-arm outside dismissal'
        window.search_text.Text = 'Searching'
        window.search_text.Focus()
        window.search_text.Select(1, 3)
        assert Mouse.Capture(window.search_text)
        Mouse.Capture(None)
        settle_pointer_layout(window.Content)
        assert Mouse.Captured == window
        assert window.search_text.SelectionStart == 1 and window.search_text.SelectionLength == 3
        window.search_text.Clear()
        menu = ContextMenu()
        item = MenuItem()
        item.Header = 'Copy'
        menu.Items.Add(item)
        window.search_text.ContextMenu = menu
        menu.PlacementTarget = window.search_text
        menu.IsOpen = True
        settle_pointer_layout(window.Content)
        assert menu.IsOpen and Mouse.Captured == menu
        window.pointer_down(window, PointerArgs(-20, -20))
        assert window.IsVisible, 'An owned context-menu click must not dismiss the window'
        menu.IsOpen = False
        settle_pointer_layout(window.Content)
        assert Mouse.Captured == window, 'Outside dismissal must re-arm after the menu closes'
        # WPF also raises opening for surfaces with no actual menu. Exercise
        # that routed event rather than pretending a popup exists in state.
        from System import Array, Object
        from System.Reflection import BindingFlags
        from System.Windows.Controls import ContextMenuEventArgs
        constructors = clr.GetClrType(ContextMenuEventArgs).GetConstructors(
            BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public)
        opening = next(ctor for ctor in constructors if len(ctor.GetParameters()) == 2)
        assert button.ContextMenu is None
        button.RaiseEvent(opening.Invoke(Array[Object]([button, True])))
        settle_pointer_layout(window.Content)
        assert not window._context_menu_open, 'A null-menu right-click must not suspend pointer handling'
        window.pointer_down(window, PointerArgs(40, 40))
        assert window._drag_origin is not None, 'Dragging remains armed after a null-menu right-click'
        window.pointer_up(window, PointerArgs(40, 40))
        window._dragged = True
        window.command_clicked(button, None)
        assert window.IsVisible and window.result.is_cancelled
        toggle = window._toggle_buttons['flag']
        toggle.IsChecked = True
        window.switch_clicked(toggle, None)
        assert not toggle.IsChecked and not window.state.switches[0].IsChecked
        class KeyArgs(object):
            Key = Key.Tab
        window.on_key_down(window, KeyArgs())
        assert not window._dragged, 'Keyboard commands remain usable after dragging'
        outside = PointerArgs(-20, -20)
        window.pointer_down(window, outside)
        assert outside.Handled and not window.IsVisible and window.result.is_cancelled
        assert Mouse.Captured is None
    finally:
        window.Close()

    owner = Window()
    owner.Title = 'Owned modal pointer fixture'
    owner.Width, owner.Height = 240, 120
    window = None
    failures = []

    def cancel_modal():
        try:
            assert ComponentDispatcher.IsThreadModal, 'Fixture must exercise the ShowDialog modal input loop'
            assert Mouse.Captured == window, 'Modal switch must own subtree capture'
            # Move only the fixture away from the real cursor, then dispatch a
            # real routed right-button event. No desktop pointer is injected.
            cursor = window.PointToScreen(Mouse.GetPosition(window))
            window.Left, window.Top = cursor.X + 100, cursor.Y + 100
            settle_pointer_layout(window.Content)
            event = MouseButtonEventArgs(Mouse.PrimaryDevice, Environment.TickCount, MouseButton.Right)
            event.RoutedEvent = Mouse.PreviewMouseDownEvent
            window.RaiseEvent(event)
            assert event.Handled, 'Routed outside right-click must be consumed'
        except Exception as error:
            failures.append(error)
            window.Close()

    try:
        owner.Show()
        owner.Activate()
        window = create_command_switch('Modal pointer fixture', [ActionChoice('run', 'Run')], owner=owner)
        window.ContentRendered += lambda sender, args: window.Dispatcher.BeginInvoke(
            DispatcherPriority.Background, Action(cancel_modal))
        window.ShowDialog()
        assert not failures, failures
        assert window.result.is_cancelled and owner.IsEnabled
        assert Mouse.Captured is None
    finally:
        if window is not None:
            window.Close()
        owner.Close()
    print('Command Switch shown pointer fixture: subtree/child capture, text selection/context menu, outside routed right-click, modal owner, drag-click suppression and keyboard recovery passed; native drag remains a physical-input check.')


validate_command_switch_pointer()
