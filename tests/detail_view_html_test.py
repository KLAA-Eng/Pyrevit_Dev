from __future__ import unicode_literals

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.detail_view_html import render_detail_html


class RenderDetailHtmlTests(unittest.TestCase):
    def test_renders_escaped_title_and_relative_encoded_artifact_links(self):
        html = render_detail_html('1 <Wall & Detail>', 'detail photo.jpg', 'detail.pdf')

        self.assertIn('<title>1 &lt;Wall &amp; Detail&gt;</title>', html)
        self.assertIn('src="detail%20photo.jpg"', html)
        self.assertIn('href="detail.pdf"', html)
        self.assertIn('alt="Preview of 1 &lt;Wall &amp; Detail&gt;"', html)
        self.assertNotIn('href="/', html)
        self.assertNotIn('src="/', html)

    def test_rejects_absolute_or_non_file_artifact_names(self):
        with self.assertRaises(ValueError):
            render_detail_html('Wall Detail', '../detail.jpg', 'detail.pdf')
        with self.assertRaises(ValueError):
            render_detail_html('Wall Detail', 'detail.jpg', 'folder/detail.pdf')


if __name__ == '__main__':
    unittest.main()
