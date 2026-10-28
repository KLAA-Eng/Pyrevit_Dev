"""Find boxes near a point without re-querying Revit for every hanger.

Framing is collected once per run; each member's model bounding box is put in
a plan grid so the members near one hanger come from a few grid cells. The
near test matches Revit's BoundingBoxIntersectsFilter: boxes that touch or
overlap the search box (min/max corners in feet).
"""

from __future__ import division

import math


CELL_FT = 6.0


def _cells(low, high, cell):
    for i in range(int(math.floor(low[0] / cell)), int(math.floor(high[0] / cell)) + 1):
        for j in range(int(math.floor(low[1] / cell)), int(math.floor(high[1] / cell)) + 1):
            yield i, j


def boxes_intersect(low_a, high_a, low_b, high_b):
    return all(low_a[k] <= high_b[k] and low_b[k] <= high_a[k] for k in range(3))


class BoxIndex(object):
    """Items with (x, y, z) min/max boxes, queried by search box."""

    def __init__(self, cell=CELL_FT):
        self.cell = cell
        self.grid = {}
        self.items = []

    def add(self, item, low, high):
        index = len(self.items)
        self.items.append((item, low, high))
        for key in _cells(low, high, self.cell):
            self.grid.setdefault(key, []).append(index)

    def near(self, low, high):
        """Items whose box touches or overlaps the search box, in insertion order."""
        seen, hits = set(), set()
        for key in _cells(low, high, self.cell):
            for index in self.grid.get(key, ()):
                if index not in seen:
                    seen.add(index)
                    _item, item_low, item_high = self.items[index]
                    if boxes_intersect(item_low, item_high, low, high):
                        hits.add(index)
        return [self.items[i][0] for i in sorted(hits)]
