"""Failure-case checks for catalog validation."""
import tempfile
import unittest
from pathlib import Path

from validate_catalog import validate


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.skill = self.root / 'skills/sociuu-example/SKILL.md'
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text('---\nname: sociuu-example\ndescription: Example\n---\n')
        (self.root / 'README.md').write_text('# Catalog\n')
        (self.root / 'docs').mkdir()
        (self.root / 'docs/guide.md').write_text('guide\n')

    def test_accepts_valid_catalog(self):
        self.assertEqual(validate(self.root), [])

    def test_rejects_missing_dependency_and_relative_link(self):
        with self.skill.open('a') as stream:
            stream.write('Use sociuu-missing and [guide](missing.md).\n')
        errors = validate(self.root)
        self.assertTrue(any('unresolved package name sociuu-missing' in e for e in errors))
        self.assertTrue(any('broken relative link missing.md' in e for e in errors))

    def test_rejects_wrong_skill_identity(self):
        self.skill.write_text('---\nname: wrong\ndescription: Example\n---\n')
        self.assertTrue(any('mismatched skill name' in e for e in validate(self.root)))

    def test_rejects_absolute_link_even_when_it_exists(self):
        target = self.root / 'docs/guide.md'
        (self.root / 'README.md').write_text(f'[guide]({target})\n')
        self.assertTrue(any('nonportable link' in e for e in validate(self.root)))

    def test_rejects_existing_target_outside_package(self):
        with tempfile.TemporaryDirectory(dir=self.root.parent) as directory:
            target = Path(directory) / 'outside.md'
            target.write_text('outside\n')
            relative = f'../{Path(directory).name}/outside.md'
            (self.root / 'README.md').write_text(f'[outside]({relative})\n')
            self.assertTrue(any('nonportable link' in e for e in validate(self.root)))


if __name__ == '__main__':
    unittest.main()
