import unittest

from lib.carbon_gwp.workflow import (
    DEFAULT_SCHEDULE_NAMES,
    clean_schedule_title,
    has_exportable_cells,
    safe_text,
    uniquify_worksheet_names,
    worksheet_name_for_schedule,
)
from lib.carbon_gwp.chart import (
    GWP_CHART_UNIT,
    VOLUME_CHART_UNIT,
    chart_canvas_height_inches,
    chart_percent,
    chart_slices_from_export_rows,
    chart_total,
    fallback_chart_color,
    format_chart_amount,
    format_chart_detail,
    format_chart_label,
    format_chart_table_amount,
)


class CarbonGwpWorkflowTests(unittest.TestCase):
    def test_default_schedules_include_project_material_takeoff(self):
        self.assertEqual(
            [
                'z_Project Material Takeoff',
                '2x Wood Wall Volume',
                'Composite Deck Volume',
            ],
            DEFAULT_SCHEDULE_NAMES,
        )

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

    def test_chart_slices_ignore_columns_after_the_export_contract(self):
        slices, skipped = chart_slices_from_export_rows([
            ['ConcreteGWP', '1200.4', 450, 'ignored label', '#4e79a7'],
            ['SteelGWP', 350, 210, 'also ignored', 'not a color'],
        ])

        self.assertEqual([], skipped)
        self.assertEqual('Concrete', slices[0]['display_label'])
        self.assertEqual('#D9D9D9', slices[0]['color'])
        self.assertEqual('Steel', slices[1]['display_label'])
        self.assertEqual('#558ED5', slices[1]['color'])
        self.assertTrue(all(item['color_source'] == 'fixed material palette'
                            for item in slices))

    def test_chart_slices_use_material_colors_when_excel_does_not_override_them(self):
        slices, skipped = chart_slices_from_export_rows([
            ['Concrete Floor', 100],
            ['Masonry Wall', 100],
            ['Wood Framing', 100],
            ['Steel Beam', 100],
        ])

        self.assertEqual([], skipped)
        self.assertEqual(
            ['#D9D9D9', '#7F7F7F', '#9BBB59', '#558ED5'],
            [item['color'] for item in slices],
        )

    def test_volume_slices_read_only_column_c_and_skip_only_invalid_volume_rows(self):
        slices, skipped = chart_slices_from_export_rows([
            ['ConcreteGWP', 1000, 3500, 'ignored', '#000000'],
            ['MasonryGWP', 250, 0, 'ignored', '#FFFFFF'],
            ['WoodGWP', 125, 475, 'ignored', '#FF0000'],
        ], value_column=2, measure_name='material volume')

        self.assertEqual(['Concrete', 'Wood'],
                         [item['display_label'] for item in slices])
        self.assertEqual([3500.0, 475.0], [item['value'] for item in slices])
        self.assertEqual(['non-positive material volume value'],
                         [item['reason'] for item in skipped])

    def test_chart_slices_skip_invalid_values_without_losing_valid_rows(self):
        slices, skipped = chart_slices_from_export_rows([
            ['GWP Concrete', '1,200'],
            ['', 100],
            ['GWP Wood', ''],
            ['GWP Steel', 'invalid'],
            ['GWP Deck', 0],
            ['GWP Rebar', -10],
        ])

        self.assertEqual(1, len(slices))
        self.assertEqual(1200.0, slices[0]['value'])
        self.assertEqual(
            ['blank source name', 'blank GWP value', 'non-numeric GWP value',
             'non-positive GWP value', 'non-positive GWP value'],
            [item['reason'] for item in skipped],
        )
        self.assertEqual('GWP Wood', skipped[1]['source_name'])
        self.assertEqual('Wood', skipped[1]['display_label'])

    def test_chart_totals_percentages_and_amounts_follow_display_contract(self):
        slices, skipped = chart_slices_from_export_rows([
            ['ConcreteGWP', 1000, 80],
            ['SteelGWP', 250, 20],
        ])

        self.assertEqual([], skipped)
        self.assertEqual(1250.0, chart_total(slices))
        self.assertEqual(80.0, chart_percent(slices[0]['value'], chart_total(slices)))
        self.assertEqual(u'1,234 kgCO\u2082e', format_chart_amount(1233.6))
        self.assertEqual(
            u'1,000 kgCO\u2082e \u2022 80.0%',
            format_chart_detail(slices[0], chart_total(slices)),
        )
        self.assertEqual(
            u'Concrete\n1,000 kgCO\u2082e \u2022 80.0%',
            format_chart_label(slices[0], chart_total(slices)),
        )
        self.assertEqual(u'1,250 CF', format_chart_amount(1250, VOLUME_CHART_UNIT))
        self.assertEqual('1233.60', format_chart_table_amount(1233.6))
        self.assertEqual(GWP_CHART_UNIT, u'kgCO\u2082e')

    def test_chart_canvas_grows_after_six_materials(self):
        self.assertEqual(4.75, chart_canvas_height_inches(6))
        self.assertEqual(5.40, chart_canvas_height_inches(7))
        self.assertEqual(6.70, chart_canvas_height_inches(9))


if __name__ == '__main__':
    unittest.main()
