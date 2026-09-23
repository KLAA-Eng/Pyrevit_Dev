from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.beam_reaction_declutter.workflow import (
    MAX_MOVE_STEPS,
    boxes_overlap,
    is_marker_color,
    is_reaction_family,
    should_defer_to_other_tag,
    steps_to_clear_overlap,
)


class BeamReactionDeclutterWorkflowTests(unittest.TestCase):
    def test_reaction_family_match_is_case_insensitive_and_safe(self):
        self.assertTrue(is_reaction_family('Structural Framing Reaction Tag'))
        self.assertTrue(is_reaction_family('REACTION END'))
        self.assertFalse(is_reaction_family('Beam Mark'))
        self.assertFalse(is_reaction_family(None))

    def test_boxes_require_overlap_beyond_the_graph_tolerance(self):
        first = (0.0, 0.0, 1.0, 1.0)

        self.assertTrue(boxes_overlap(first, (0.98, 0.0, 1.5, 1.0)))
        self.assertFalse(boxes_overlap(first, (0.995, 0.0, 1.5, 1.0)))
        self.assertFalse(boxes_overlap(first, None))

    def test_steps_to_clear_overlap_returns_the_first_clear_step(self):
        steps = steps_to_clear_overlap(
            (0.0, 0.0, 0.2, 1.0),
            (0.1, 0.0, 0.3, 1.0),
            (0.2, 0.0),
        )

        self.assertEqual(2, steps)

    def test_steps_to_clear_overlap_reports_the_capped_unresolved_case(self):
        steps = steps_to_clear_overlap(
            (0.0, 0.0, 1.0, 1.0),
            (0.5, 0.0, 20.0, 1.0),
            (0.2, 0.0),
        )

        self.assertIsNone(steps)
        self.assertEqual(8, MAX_MOVE_STEPS)

    def test_steps_to_clear_overlap_leaves_a_clear_tag_at_zero_steps(self):
        self.assertEqual(0, steps_to_clear_overlap(
            (0.0, 0.0, 1.0, 1.0),
            (2.0, 0.0, 3.0, 1.0),
            (0.2, 0.0),
        ))

    def test_more_vertical_beam_receives_priority(self):
        self.assertTrue(should_defer_to_other_tag(0.25, 0.75))
        self.assertFalse(should_defer_to_other_tag(0.75, 0.25))
        self.assertFalse(should_defer_to_other_tag(0.75, 0.75))

    def test_only_the_exact_dynamo_red_is_a_reset_marker(self):
        self.assertTrue(is_marker_color(254, 0, 0))
        self.assertFalse(is_marker_color(255, 0, 0))
        self.assertFalse(is_marker_color(254, 1, 0))


if __name__ == '__main__':
    unittest.main()
