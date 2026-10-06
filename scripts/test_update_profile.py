import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import URLError

from update_profile import ROOT, render, update


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / '.github/README.template.md').read_text(encoding='utf-8')
        self.profile = {
            'login': 'Pegoku', 'name': 'Pere Gomila',
            'location': 'Eindhoven, Netherlands', 'company': '@InnoFluidics ',
        }

    def test_live_fields_and_curated_content(self):
        result = render(self.template, self.profile)
        self.assertIn('Based in   Eindhoven, Netherlands', result)
        self.assertIn('Company    @InnoFluidics\n', result)
        self.assertIn('KiCad / FreeCAD', result)
        self.assertNotIn('{{', result)

    def test_missing_optional_fields_preserve_logo(self):
        result = render(self.template, {'login': 'Pegoku', 'name': None, 'location': None})
        self.assertTrue(result.startswith('# Pegoku\n'))
        self.assertNotIn('Based in', result)
        self.assertNotIn('Company', result)
        source_rows = self.template.split('```text\n')[1].split('\n```')[0].splitlines()
        output_rows = result.split('```text\n')[1].split('\n```')[0].splitlines()
        self.assertEqual([r[:36].rstrip() for r in source_rows],
                         [r[:36].rstrip() for r in output_rows])

    def test_multiline_and_markdown_in_profile_fields(self):
        self.profile.update(name='Pere *Gomila*', company='Example\n```\nCompany')
        result = render(self.template, self.profile)
        self.assertTrue(result.startswith('# Pere \\*Gomila\\*\n'))
        self.assertEqual(result.count('```'), 2)
        self.assertIn("Company    Example ''' Company", result)

    def test_no_write_on_network_or_data_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'README.md'
            output.write_text('existing README')
            template = ROOT / '.github/README.template.md'
            with patch('update_profile.fetch_profile', side_effect=URLError('offline')):
                with self.assertRaises(URLError):
                    update('Pegoku', template, output)
            self.assertEqual(output.read_text(), 'existing README')
            with patch('update_profile.fetch_profile', return_value={'login': 'Pegoku', 'company': []}):
                with self.assertRaises(ValueError):
                    update('Pegoku', template, output)
            self.assertEqual(output.read_text(), 'existing README')

    def test_identical_profile_does_not_rewrite_readme(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'README.md'
            with patch('update_profile.fetch_profile', return_value=self.profile):
                self.assertTrue(update('Pegoku', ROOT / '.github/README.template.md', output))
                before = output.stat().st_mtime_ns
                self.assertFalse(update('Pegoku', ROOT / '.github/README.template.md', output))
                self.assertEqual(before, output.stat().st_mtime_ns)


if __name__ == '__main__':
    unittest.main()
