import unittest

from lib.concrete_mix_schedule_header import (
    TEMPLATE_ELEMENTS,
    build_mix_history_schedule_grid,
    build_write_plan,
    classify_template_reconciliation,
    element_match_key,
    format_fractional_inches,
    insertion_anchor_offset,
    mix_history_column_map,
    normalize_grid,
    parse_a1_range,
    range_size,
    safe_cell_text,
    template_element_records,
)


class ConcreteMixScheduleHeaderTest(unittest.TestCase):
    def _pair(self, element, row_offset=0):
        return {
            'element': element,
            'key': element_match_key(element),
            'row_offset': row_offset,
            'grid': [[element], ['']],
        }

    def test_parse_a1_range(self):
        self.assertEqual((1, 1, 3, 4), parse_a1_range('A1:D3'))
        self.assertEqual((10, 27, 10, 27), parse_a1_range('$AA$10'))

    def test_range_size(self):
        self.assertEqual((6, 8), range_size('A1:H6'))

    def test_normalize_grid_pads_to_range_size(self):
        grid = normalize_grid([[1.0, None], ['A']], row_count=2, column_count=3)
        self.assertEqual([['1', '', ''], ['A', '', '']], grid)

    def test_safe_cell_text_keeps_decimal_when_needed(self):
        self.assertEqual('3', safe_cell_text(3.0))
        self.assertEqual('3.25', safe_cell_text(3.25))

    def test_format_fractional_inches_formats_numeric_values(self):
        self.assertEqual('3/4"', format_fractional_inches(0.75))
        self.assertEqual('1"', format_fractional_inches(1.0))
        self.assertEqual('1 1/2"', format_fractional_inches(1.5))

    def test_format_fractional_inches_leaves_non_numeric_or_formatted_text(self):
        self.assertEqual('-', format_fractional_inches('-'))
        self.assertEqual('3/4"', format_fractional_inches('3/4"'))

    def test_build_write_plan_uses_absolute_header_coordinates(self):
        plan = build_write_plan([['A', 'B'], ['C', '']], first_row=5, first_column=2)
        self.assertEqual(
            [
                {'row': 5, 'column': 2, 'row_offset': 0, 'column_offset': 0, 'text': 'A'},
                {'row': 5, 'column': 3, 'row_offset': 0, 'column_offset': 1, 'text': 'B'},
                {'row': 6, 'column': 2, 'row_offset': 1, 'column_offset': 0, 'text': 'C'},
                {'row': 6, 'column': 3, 'row_offset': 1, 'column_offset': 1, 'text': ''},
            ],
            plan,
        )

    def test_mix_history_column_map_ignores_delete_column(self):
        headers = [
            'Elements', "f'c (psi)", 'Cement Type', 'Max (w/c)', 'Max Agg',
            'Air Content (%)', 'Slump', '(F)', '(S)', '(W)', '(C)', 'Delete',
        ]
        mapping = mix_history_column_map(headers)
        self.assertEqual(0, mapping['element'])
        self.assertEqual(1, mapping['strength'])
        self.assertEqual(7, mapping['freeze_thaw'])
        self.assertEqual(8, mapping['sulfate'])
        self.assertEqual(9, mapping['water'])
        self.assertEqual(10, mapping['corrosion'])
        self.assertNotIn('delete', mapping)

    def test_build_mix_history_schedule_grid_maps_one_excel_row_to_two_revit_rows(self):
        headers = [
            'Elements', "f'c (psi)", 'Cement Type', 'Max (w/c)', 'Max Agg',
            'Air Content (%)', 'Slump', '(F)', '(S)', '(W)', '(C)', 'Delete',
        ]
        rows = [[
            'Footings', 4000, 'IL/I-II', '-', 0.75, '-', '-', 'F0', 'S0', 'W0', 'C2', 'Delete',
        ]]
        grid, mapping = build_mix_history_schedule_grid(headers, rows, max_mix_rows=4)
        self.assertEqual('Footings', grid[0][0])
        self.assertEqual('4000', grid[0][2])
        self.assertEqual('IL/I-II', grid[0][3])
        self.assertEqual('-', grid[0][4])
        self.assertEqual('3/4"', grid[0][5])
        self.assertEqual('-', grid[0][6])
        self.assertEqual('-', grid[0][7])
        self.assertEqual('F0', grid[0][8])
        self.assertEqual('C2', grid[0][9])
        self.assertEqual('S0', grid[1][8])
        self.assertEqual('W0', grid[1][9])
        self.assertEqual('', grid[0][10])
        self.assertEqual('', grid[1][10])
        self.assertEqual(4, len(grid))
        self.assertEqual(11, len(grid[0]))
        self.assertEqual(10, mapping['corrosion'])

    def test_element_match_key_ignores_parenthetical_suffix(self):
        self.assertEqual(
            element_match_key('Interior Slab on Grade'),
            element_match_key('Interior Slab on Grade (SOG)'),
        )

    def test_element_match_key_normalizes_superscript_digits(self):
        self.assertEqual(
            element_match_key('Other 5'),
            element_match_key('Other ⁵'),
        )

    def test_template_elements_expose_all_known_gn03_rows(self):
        records = template_element_records()
        self.assertEqual(15, len(records))
        self.assertEqual('Drilled Piers', records[0]['element'])
        self.assertEqual('Other ⁵', records[-1]['element'])
        self.assertEqual(
            len(TEMPLATE_ELEMENTS),
            len(set(record['key'] for record in records)),
        )

    def test_reconciliation_classifies_exact_template_match(self):
        excel_pairs = [self._pair(element, index * 2) for index, element in enumerate(TEMPLATE_ELEMENTS)]
        current_pairs = [self._pair(element, index * 2) for index, element in enumerate(TEMPLATE_ELEMENTS)]
        result = classify_template_reconciliation(excel_pairs, current_pairs)
        self.assertEqual(15, len(result['to_update']))
        self.assertEqual([], result['to_add'])
        self.assertEqual([], result['missing_from_excel'])
        self.assertEqual([], result['unknown_excel'])

    def test_reconciliation_reports_current_template_rows_missing_from_excel(self):
        excel_pairs = [self._pair('Drilled Piers', 0), self._pair('Footings', 6)]
        current_pairs = [
            self._pair('Drilled Piers', 0),
            self._pair('Pier Caps', 2),
            self._pair('Footings', 6),
        ]
        result = classify_template_reconciliation(excel_pairs, current_pairs)
        self.assertEqual(['Pier Caps'], [pair['element'] for pair in result['missing_from_excel']])
        self.assertEqual(['Drilled Piers', 'Footings'], [pair['element'] for pair in result['to_update']])

    def test_reconciliation_reports_unknown_excel_elements(self):
        result = classify_template_reconciliation(
            [self._pair('Footings', 0), self._pair('Not A Template Element', 2)],
            [self._pair('Footings', 0)],
        )
        self.assertEqual(['Not A Template Element'], [pair['element'] for pair in result['unknown_excel']])
        self.assertEqual(['Footings'], [pair['element'] for pair in result['known_excel']])

    def test_reconciliation_marks_previously_removed_excel_rows_for_add_back(self):
        result = classify_template_reconciliation(
            [self._pair('Pier Caps', 0), self._pair('Footings', 2)],
            [self._pair('Footings', 0)],
        )
        self.assertEqual(['Pier Caps'], [pair['element'] for pair in result['to_add']])
        self.assertEqual(['Footings'], [pair['element'] for pair in result['to_update']])

    def test_insertion_anchor_uses_next_existing_template_row(self):
        current_pairs = [self._pair('Drilled Piers', 0), self._pair('Footings', 2)]
        anchor = insertion_anchor_offset(element_match_key('Pier Caps'), current_pairs, notes_start_offset=4)
        self.assertEqual(2, anchor)

    def test_insertion_anchor_falls_back_to_notes_anchor_for_last_missing_row(self):
        current_pairs = [self._pair('Drilled Piers', 0), self._pair('Footings', 2)]
        anchor = insertion_anchor_offset(element_match_key('Other ⁵'), current_pairs, notes_start_offset=4)
        self.assertEqual(4, anchor)


if __name__ == '__main__':
    unittest.main()
