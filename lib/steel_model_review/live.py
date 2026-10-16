"""Modeless report controller with Revit External Event and document guards."""

from pyrevit import DB, UI, forms
from System import AppDomain, EventHandler

from steel_model_review.browser import ReviewWindow
from steel_model_review import view as review_view


class ReviewSession(UI.IExternalEventHandler):
    """Keep report interaction and all Revit writes on their supported boundaries.

    Callbacks supply the command's run, freshness, persistence, navigation,
    grid assignment, coverage and failure reporting without duplicating rules.
    """

    def __init__(self, uiapp, document, xaml, snapshot, callbacks, registry_key):
        self.document = document
        self.application = uiapp.Application
        self.uiapp = uiapp
        self.callbacks = callbacks
        self.registry_key = registry_key
        self.snapshot = snapshot
        self.window = None
        self.closed = False
        self.closing = False
        self.writing = False
        self.document_dirty = True
        self.colors_dirty = True
        self.scope_dirty = True
        self.actions = []
        self.stale = callbacks['fresh'](snapshot) is False
        self.view_uid = snapshot.get('review_view_uid')
        self.last_plan = None
        self.event = UI.ExternalEvent.Create(self)
        self.window = ReviewWindow(xaml, snapshot, self.stale, self.request)
        self.window.Closed += self._closed
        self._changed_handler = EventHandler[DB.Events.DocumentChangedEventArgs](self._changed)
        self._closing_handler = EventHandler[DB.Events.DocumentClosingEventArgs](self._document_closing)
        self._view_handler = EventHandler[UI.Events.ViewActivatedEventArgs](self._view_activated)
        self.application.DocumentChanged += self._changed_handler
        self.application.DocumentClosing += self._closing_handler
        self.uiapp.ViewActivated += self._view_handler

    def show(self):
        self.window.Show()
        self.request('view', None)

    def GetName(self):
        return 'KL&A Model Checker report and 3D review'

    def request(self, action, row):
        """Coalesce filter changes; retain deliberate workflow actions in order."""
        if self.closed or (self.closing and action != 'close'):
            return
        if action == 'close':
            self.closing = True
            self.actions = [('close', None)]
        elif action == 'colors':
            self.colors_dirty = True
        elif action == 'refresh':
            self.document_dirty = True
        else:
            self.actions.append((action, row))
        try:
            result = str(self.event.Raise())
        except Exception as error:
            self.actions = []
            if self.window:
                self.window.view_status.Text = 'Could not queue a Revit update: {0}'.format(error)
            return
        if result not in ('Accepted', 'Pending') and self.window:
            self.actions = []
            self.window.view_status.Text = 'Revit deferred this request ({0}); retry when idle.'.format(result)

    def _closed(self, sender, args):
        self.request('close', None)

    def _changed(self, sender, args):
        if not self.writing and args.GetDocument().Equals(self.document):
            self.request('refresh', None)

    def _document_closing(self, sender, args):
        if not self.closing and args.Document.Equals(self.document):
            self.window.Close()

    def _view_activated(self, sender, args):
        if not self.closed and not self.closing:
            self.request('refresh', None)

    def _dispose(self):
        """Unsubscribe inside API context; no queued request may outlive the UI."""
        self.application.DocumentChanged -= self._changed_handler
        self.application.DocumentClosing -= self._closing_handler
        self.uiapp.ViewActivated -= self._view_handler
        self.closed = True
        self.actions = []
        AppDomain.CurrentDomain.SetData(self.registry_key, None)
        self.event.Dispose()

    def Execute(self, uiapp):
        """Validate document ownership, handle UI requests, then update graphics."""
        if self.closed:
            return
        if self.closing:
            self._dispose()
            return
        if not self.document.IsValidObject:
            self.window.Close()
            self._dispose()
            return
        uidoc = uiapp.ActiveUIDocument
        if uidoc is None or not uidoc.Document.Equals(self.document):
            self.actions = []
            self.window.view_status.Text = 'Activate the report\'s project to update its review view.'
            return
        self.window.IsEnabled = False
        try:
            actions, self.actions = self.actions, []
            if self.document_dirty or any(a == 'accept' for a, _r in actions):
                self.stale = not self.callbacks['fresh'](self.snapshot)
                self.document_dirty = False
                self.window.set_stale(self.stale)
            open_view = False
            for action, row in actions:
                if self.closing:
                    break
                if action == 'view':
                    open_view = True
                    self.scope_dirty = True
                    self.colors_dirty = True
                elif action == 'rerun':
                    new = self.callbacks['run'](self.snapshot)
                    if new['state'] == 'Complete':
                        self.snapshot = new
                        self.stale = not self.callbacks['fresh'](new)
                        self.scope_dirty = self.colors_dirty = True
                        self.window.set_snapshot(new, self.stale)
                    else:
                        self.window.view_status.Text = 'Rerun cancelled; previous report and view preserved.'
                elif action == 'select':
                    self.callbacks['navigate'](row)
                elif action == 'coverage':
                    self.callbacks['coverage'](self.snapshot)
                elif action == 'grids':
                    self.callbacks['grids'](row, self.snapshot)
                    self.stale = not self.callbacks['fresh'](self.snapshot)
                    self.window.set_stale(self.stale)
                elif action in ('accept', 'reopen'):
                    self._review(action, row)
            if self.closing:
                self._dispose()
                return
            if self.colors_dirty or self.scope_dirty:
                self._update_view(uidoc, open_view)
            self.callbacks['save'](self.snapshot)
        except Exception:
            self.window.view_status.Text = 'View/report update failed. Expand the failure dialog for details.'
            self.callbacks['failure']()
        finally:
            if not self.closed:
                self.window.IsEnabled = True

    def _review(self, action, row):
        if not any(current is row for current in self.snapshot['rows']):
            self.window.view_status.Text = 'The report changed; select a finding in the current report.'
            return
        if action == 'accept':
            if self.stale or self.snapshot['state'] != 'Complete':
                forms.alert('Rerun the checks before accepting a stale or incomplete report.',
                            title='Model Checker')
                return
            if row['severity'] not in ('Critical', 'Error', 'Warning'):
                forms.alert('Only Critical, Error, or Warning findings may be accepted.',
                            title='Model Checker')
                return
            reason = forms.ask_for_string(prompt='Reason this condition is intentional:',
                                           title='Model Checker')
            if not reason or not reason.strip():
                return
            row.update(status='Accepted exception', exception=reason.strip())
        else:
            row.update(status='Open', exception='')
        self.window.set_snapshot(self.snapshot, self.stale)
        self.colors_dirty = True

    def _update_view(self, uidoc, open_view):
        """Create/isolate once per run; write only changed colors thereafter."""
        if self.snapshot['state'] != 'Complete' or not review_view.scope_members(self.snapshot):
            self.window.view_status.Text = 'No 3D view created: a complete report with extracted members is required.'
            self.colors_dirty = self.scope_dirty = False
            return
        view = self.document.GetElement(self.view_uid) if self.view_uid else None
        if view is not None and (not isinstance(view, DB.View3D) or view.IsTemplate):
            raise ValueError('The saved review view is not an editable 3D view.')
        plan = review_view.color_plan(self.snapshot, self.window.visible_rows())
        reset_scope = self.scope_dirty or view is None
        delta = plan if reset_scope or self.last_plan is None else dict(
            (uid, color) for uid, color in plan.items() if self.last_plan.get(uid) != color)
        if reset_scope or delta:
            transaction = DB.Transaction(self.document, 'Model Checker review view')
            self.writing = True
            try:
                transaction.Start()
                if view is None:
                    phase_id = self.snapshot.get('phase_id')
                    if phase_id is None:
                        first = next(iter(review_view.scope_members(self.snapshot).values()))
                        phase_id = first.get('scope', {}).get('phase_id')
                    view = review_view.create(self.document, DB, phase_id)
                if reset_scope:
                    phase_id = self.snapshot.get('phase_id')
                    if phase_id is not None:
                        view.get_Parameter(DB.BuiltInParameter.VIEW_PHASE).Set(DB.ElementId(phase_id))
                    review_view.isolate(self.document, DB, view, self.snapshot)
                review_view.apply_colors(self.document, DB, view, delta)
                if transaction.Commit() != DB.TransactionStatus.Committed:
                    raise ValueError('Revit did not commit the review-view update.')
            except Exception:
                if transaction.GetStatus() == DB.TransactionStatus.Started:
                    transaction.RollBack()
                raise
            finally:
                self.writing = False
                transaction.Dispose()
        self.view_uid = view.UniqueId
        self.snapshot['review_view_uid'] = self.view_uid
        self.last_plan = plan
        self.colors_dirty = self.scope_dirty = False
        self.window.view_status.Text = review_view.visibility_summary(
            self.document, DB, view, self.snapshot)
        if open_view:
            uidoc.RequestViewChange(view)
