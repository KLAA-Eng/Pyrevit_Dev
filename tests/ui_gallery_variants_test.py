"""Family preview choices remain explicit and survive Gallery refreshes."""
import unittest

from lib.ui_gallery.variants import PreviewMemory, preview_launcher, variant_labels


def family():
    return dict(id='dialog-message', title='Shared dialog - Message',
                states=['Normal', 'Empty', 'Warning'], variants=[
                    dict(id='dialog-message-plain', label='Without Details'),
                    dict(id='dialog-message', label='With Details')])


class GalleryVariantTests(unittest.TestCase):
    def test_variant_selection_returns_exact_adapter_without_mutating_family(self):
        entry = family()
        launcher = preview_launcher(entry, 'dialog-message')
        self.assertEqual('dialog-message', launcher['id'])
        self.assertNotIn('variants', launcher)
        self.assertIn('With Details', launcher['title'])
        self.assertEqual(2, len(entry['variants']))
        self.assertEqual('Without Details, With Details', variant_labels(entry))

    def test_unknown_variant_is_rejected_instead_of_becoming_a_launcher(self):
        with self.assertRaises(ValueError):
            preview_launcher(family(), 'unreviewed-window')

    def test_memory_keeps_family_choices_across_row_reconstruction(self):
        memory = PreviewMemory()
        self.assertEqual(('dialog-message-plain', 'Normal'), memory.get(family()))
        memory.set(family(), 'dialog-message', 'Warning')
        self.assertEqual(('dialog-message', 'Warning'), memory.get(family()))
        other = dict(id='other', title='Other', states=['Normal'])
        self.assertEqual(('other', 'Normal'), memory.get(other))
        self.assertEqual(('dialog-message', 'Warning'), memory.get(family()))

    def test_missing_state_falls_back_to_normal_and_deferred_rows_have_no_state(self):
        memory = PreviewMemory()
        entry = family()
        memory.set(entry, 'dialog-message', 'Warning')
        entry['states'] = ['Normal', 'Empty']
        self.assertEqual(('dialog-message', 'Normal'), memory.get(entry))
        entry['states'] = []
        self.assertEqual(('dialog-message', None), memory.get(entry))

    def test_default_rows_and_invalid_memory_values(self):
        entry = dict(id='fixture', title='Fixture', states=['Normal'])
        self.assertEqual('Default', variant_labels(entry))
        self.assertEqual('fixture', preview_launcher(entry)['id'])
        memory = PreviewMemory()
        with self.assertRaises(ValueError):
            memory.set(entry, 'fixture', 'Warning')
        with self.assertRaises(ValueError):
            memory.set(entry, 'foreign', 'Normal')
