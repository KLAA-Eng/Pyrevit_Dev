# -*- coding: utf-8 -*-
"""Apply exact view/sheet changes with one undo item and per-item rollback."""

from Autodesk.Revit.DB import SubTransaction, Transaction, TransactionStatus
from Autodesk.Revit.Exceptions import ArgumentException

from find_replace.workflow import new_result, record


class ExactTargetError(Exception):
    pass


def _message(error):
    try:
        return unicode(error)
    except NameError:
        return str(error)


def _rollback_started(transaction):
    if transaction.GetStatus() == TransactionStatus.Started:
        transaction.RollBack()


def _mark_batch_failure(result, entries, message, reason="Batch transaction did not commit"):
    result["error"] = message
    changed = result["changed"]
    result["changed"] = []
    for label, unused in changed:
        record(result, "failed", label, reason)
    accounted = set(label for kind in ("unchanged", "skipped", "failed")
                    for label, unused in result[kind])
    for entry in entries:
        if entry["label"] not in accounted:
            record(result, "failed", entry["label"], reason)


def apply_batch(doc, action, entries):
    """Entries have label, changes [(property, exact target)], and optional issue."""
    result = new_result(action)
    to_change = []
    for entry in entries:
        if entry.get("issue"):
            record(result, "skipped", entry["label"], entry["issue"])
        elif entry["changes"]:
            to_change.append(entry)
        else:
            record(result, "unchanged", entry["label"])

    if not to_change:
        return result

    try:
        transaction = Transaction(doc, action)
    except Exception as error:
        _mark_batch_failure(result, to_change,
                            "Could not create the Revit transaction: {0}".format(
                                _message(error)))
        return result
    try:
        if transaction.Start() != TransactionStatus.Started:
            raise RuntimeError("Could not start the Revit transaction")
        for entry in to_change:
            sub = SubTransaction(doc)
            try:
                if sub.Start() != TransactionStatus.Started:
                    raise RuntimeError("Could not start the item transaction")
                for field, target in entry["changes"]:
                    setattr(entry["element"], field, target)
                    if getattr(entry["element"], field) != target:
                        raise ExactTargetError("Revit did not retain the exact requested value")
                if sub.Commit() != TransactionStatus.Committed:
                    raise RuntimeError("The item transaction did not commit")
                record(result, "changed", entry["label"])
            except (ArgumentException, ExactTargetError) as error:
                _rollback_started(sub)
                record(result, "skipped", entry["label"], _message(error))
            except Exception as error:
                _rollback_started(sub)
                record(result, "failed", entry["label"], _message(error))
            finally:
                sub.Dispose()
        status = transaction.Commit()
        if status != TransactionStatus.Committed:
            reason = "Commit outcome is pending" if status == TransactionStatus.Pending else "Batch transaction did not commit"
            _mark_batch_failure(result, to_change,
                                "Batch transaction status: {0}".format(status), reason)
    except Exception as error:
        try:
            _rollback_started(transaction)
        except Exception as rollback_error:
            _mark_batch_failure(result, to_change,
                                "Rollback failed: {0}".format(_message(rollback_error)))
        else:
            _mark_batch_failure(result, to_change,
                                "Batch transaction failed: {0}".format(_message(error)))
    finally:
        try:
            transaction.Dispose()
        except Exception as error:
            cleanup = "Transaction cleanup failed: {0}".format(_message(error))
            result["error"] = (result["error"] + "; " + cleanup
                               if result["error"] else cleanup)
    return result
