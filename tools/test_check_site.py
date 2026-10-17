import tempfile
import unittest
from pathlib import Path

import check_site

HEAD = '<!doctype html><html lang="en"><head><meta charset="utf-8">' \
    '<meta name="viewport" content="width=device-width, initial-scale=1"><title>T</title></head><body>'
TAIL = '</body></html>'


class CheckSiteTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def page(self, path, body='', head=HEAD):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(head + body + TAIL, encoding='utf-8')

    def test_clean_site_passes(self):
        self.page('index.html', '<a href="/fut27/">FUT 27</a>')
        self.page('fut27/index.html', '<a href="/">Home</a>')
        self.assertEqual(check_site.check(self.root), [])

    def test_missing_internal_target(self):
        self.page('index.html', '<a href="/fut27/">FUT 27</a>')
        self.assertEqual(check_site.check(self.root), ['index.html: broken link /fut27/'])

    def test_link_without_trailing_slash(self):
        self.page('index.html', '<a href="/contact">Contact</a>')
        self.page('contact/index.html')
        problems = check_site.check(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn('/contact', problems[0])

    def test_external_script_banned(self):
        self.page('index.html', '<script src="https://x.example/y.js"></script>')
        problems = check_site.check(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn('external', problems[0])

    def test_external_stylesheet_banned(self):
        head = HEAD.replace('</head>', '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=X"></head>')
        self.page('index.html', head=head)
        problems = check_site.check(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn('external', problems[0])

    def test_devero_ab_banned(self):
        for text in ['Devero AB', 'devero ab', 'DEVERO&nbsp;AB', 'Devero AB']:
            with self.subTest(text=text):
                self.page('index.html', f'<p>© 2026 {text}</p>')
                problems = check_site.check(self.root)
                self.assertEqual(len(problems), 1)
                self.assertIn('Devero AB', problems[0])

    def test_page_needs_lang_title_viewport(self):
        self.page('index.html', head='<!doctype html><html><head></head><body>')
        problems = check_site.check(self.root)
        self.assertEqual(len(problems), 3)
        joined = '\n'.join(problems)
        for word in ['lang', 'title', 'viewport']:
            self.assertIn(word, joined)

    def test_mailto_and_https_links_allowed(self):
        self.page('index.html', '<a href="mailto:hello@devero.se">Mail</a>'
                                '<a href="https://play.google.com/store">Play</a>')
        self.assertEqual(check_site.check(self.root), [])

    def test_assets_resolve_to_files(self):
        head = HEAD.replace('</head>', '<link rel="stylesheet" href="/assets/site.css"></head>')
        self.page('index.html', head=head)
        self.assertEqual(check_site.check(self.root), ['index.html: broken link /assets/site.css'])
        (self.root / 'assets').mkdir()
        (self.root / 'assets/site.css').write_text('')
        self.assertEqual(check_site.check(self.root), [])


if __name__ == '__main__':
    unittest.main()
