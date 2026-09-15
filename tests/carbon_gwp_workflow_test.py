import unittest

from lib.carbon_gwp.workflow import (
    clean_schedule_title,
    has_exportable_cells,
    parameter_value_pairs_from_export_rows,
    safe_text,
    uniquify_worksheet_names,
    validate_parameter_value_pairs,
    worksheet_name_for_schedule,
)


class CarbonGwpWorkflowTests(unittest.TestCase):
    def test_has_exportable_cells_requires_a_structural_cell(self):
        self.assertFalse(has_exportable_cells([]))
        self.assertFalse(has_exportable_cells([[], []]))
        self.assertTrue(has_exportable_cells([['']]))

    def test_safe_text_normalizes_excel_whole_numbers(self):
        self.assertEqual('42', safe_text(42.0))

    def test_clean_schedule_title_removes_dynamo_prefix_artifacts(self):
        self.assertEqual('Concrete', clean_schedule_title('Schedule = Concrete'))
        self.assertEqual('Wood Wall', clean_schedule_title('Family(Type) Wood Wall'))
        self.assertEqual('Composite Deck', clean_schedule_title(' Composite Deck '))

    def test_worksheet_name_for_schedule_adds_prefix_and_excel_safety(self):
        self.assertEqual(
            'DYN Out - Material_Area',
            worksheet_name_for_schedule('Material/Area'),
        )
        self.assertLessEqual(len(worksheet_name_for_schedule('A' * 80)), 31)

    def test_uniquify_worksheet_names_preserves_excel_limit(self):
        names = uniquify_worksheet_names([
            'DYN Out - Same Schedule Name',
            'DYN Out - Same Schedule Name',
        ])
        self.assertEqual('DYN Out - Same Schedule Name', names[0])
        self.assertEqual('DYN Out - Same Schedule Nam (2)', names[1])
        self.assertTrue(all(len(name) <= 31 for name in names))

    def test_parameter_value_pairs_read_first_two_columns(self):
        pairs, skipped = parameter_value_pairs_from_export_rows([
            ['GWP Concrete', 42.0, 'ignored'],
            ['', 'missing name'],
            ['GWP Steel', None],
        ])
        self.assertEqual(
            [
                {'row': 1, 'parameter_name': 'GWP Concrete', 'value': '42'},
                {'row': 3, 'parameter_name': 'GWP Steel', 'value': ''},
            ],
            pairs,
        )
        self.assertEqual('blank parameter name', skipped[0]['reason'])

    def test_validate_parameter_value_pairs_rejects_duplicate_names(self):
        valid, skipped = validate_parameter_value_pairs([
            {'row': 1, 'parameter_name': 'GWP Concrete', 'value': '10'},
            {'row': 2, 'parameter_name': 'gwp concrete', 'value': '11'},
        ])
        self.assertEqual(1, len(valid))
        self.assertEqual('duplicate parameter name', skipped[0]['reason'])


if __name__ == '__main__':
    unittest.main()
