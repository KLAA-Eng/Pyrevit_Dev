"""Shared Rename requests and result actions; callers own model operations."""
from __future__ import unicode_literals

from find_replace.workflow import details, new_result, summary, unresolved


def retry_elements(elements, entries, result):
    """Retry failed/skipped identities, never committed successes in a partial batch."""
    labels = set(label for kind in ('skipped', 'failed')
                 for label, reason in result[kind])
    if labels:
        return [entry['element'] for entry in entries if entry['label'] in labels]
    if result['changed']:
        # A post-commit presentation/refresh error must not reapply the rules.
        return []
    return list(elements)


def run(title, version, elements, fields, plan, execute, after_change=None,
        owner=None, dialogs_api=None):
    """Close each shared request before executing; edit only unfinished targets.

    ``plan`` snapshots labels and exact changes. ``execute`` uses apply_batch's
    accounted result contract so committed elements are excluded from retries.
    """
    if dialogs_api is None:
        from GUI import dialogs as dialogs_api
    pending = list(elements)
    last_result = None
    while pending:
        window = dialogs_api.create_rename(title, fields, version=version, owner=owner)
        window.ShowDialog()
        if window.result.is_cancelled:
            return last_result
        # Case actions intentionally ignore rules, but edits must survive a
        # failed case operation and an ensuing Edit and Retry.
        window.sync_fields()
        fields = [field.clone() for field in window.state.fields]
        request = window.result.value
        action = {'rename': 'Rename', 'upper': 'Uppercase', 'lower': 'Lowercase'}[request['operation']]
        entries = []
        try:
            entries = plan(pending, request)
        except Exception as error:
            result = new_result(action)
            result['error'] = 'Could not plan changes: {0}'.format(error)
        else:
            result = execute(action, entries)
            if result['changed'] and after_change is not None:
                try:
                    after_change()
                except Exception as error:
                    extra = 'Project Browser refresh failed: {0}'.format(error)
                    result['error'] = result['error'] + '; ' + extra if result['error'] else extra
        last_result = result
        if result['changed'] and not unresolved(result):
            return result
        pending = retry_elements(pending, entries, result)
        choices = ([dialogs_api.ActionChoice('edit_retry', 'Edit and Retry',
                    'Edit the retained rules for {0} unfinished item(s).'.format(len(pending)))]
                   if pending else [])
        report = dialogs_api.choose_action(title, choices,
            prompt=summary(result),
            content='No values changed.' if not unresolved(result) else 'Some changes could not be completed.',
            details=details(result) or 'The requested operation did not change any values.',
            buttons=('close',), severity='warning' if unresolved(result) else 'information',
            version=version, owner=owner)
        if (report.is_cancelled or not report.value
                or report.value.get('kind') != 'command'
                or report.value.get('key') != 'edit_retry'):
            return result
    return last_result
