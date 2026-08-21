import unittest

from lib.concrete_mix_schedule_header import (
    build_mix_history_schedule_grid,
    build_write_plan,
    element_match_key,
    mix_history_column_map,
    normalize_grid,
    parse_a1_range,
    range_size,
    safe_cell_text,
)


class ConcreteMixScheduleHeaderTest(unittest.TestCase):
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
        self.assertEqual('0.75', grid[0][5])
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


if __name__ == '__main__':
    unittest.main()
