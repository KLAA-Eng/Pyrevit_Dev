"""Serializable Member -> Relationship -> Check Result contracts."""

from steel_model_review.session import signature

SCHEMA_VERSION = 2
# Advance when acceptance rules change without changing the record structure.
RULESET_VERSION = 1


def member_record(source):
    """Copy normalized source facts into a versioned, host-independent member."""
    record = dict(source)
    record.update(record_type='Member', schema_version=SCHEMA_VERSION)
    return record


def relationship(member, target_member, category, end='', target_end='', **evidence):
    """Record one relationship without embedding mutable member geometry.

    Identity uses participants, end/station role and category, while measurements
    remain evidence. Model/settings fingerprints invalidate prior acceptance.
    """
    target_uid = target_member['uid'] if target_member else None
    identity = [member['uid'], str(end), target_uid, str(target_end), category]
    record = {'record_type': 'Relationship', 'schema_version': SCHEMA_VERSION,
              'relationship_id': signature(identity), 'member_uid': member['uid'],
              'target_uid': target_uid, 'end': end, 'target_end': target_end,
              'category': category, 'evidence': evidence}
    return record


def bind_result(result, relation, error_type=''):
    """Reference a relationship from a result while retaining browser fields."""
    result.update(record_type='CheckResult', schema_version=SCHEMA_VERSION,
                  member_uid=result['uid'], relationship_id=relation['relationship_id'],
                  category=relation['category'], error_type=error_type,
                  evaluation='Not evaluated' if result['severity'] == 'Not evaluated'
                  else 'Evaluated')
    result['key'] = tuple(result['key']) + (relation['relationship_id'],)
    result['result_id'] = signature(result['key'])
    return result
