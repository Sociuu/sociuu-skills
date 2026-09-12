"""Failure-case checks for catalog and distribution validation."""
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
        (self.root / 'docs/delivery-contract.md').write_text('contract\n')

    def test_accepts_matching_distribution(self):
        repository = self.root / 'consumer'
        target = repository / 'docs/agents/sociuu-delivery.md'
        target.parent.mkdir(parents=True)
        target.write_text('contract\n')
        self.assertEqual(validate(self.root, [repository]), [])

    def test_rejects_missing_dependency_and_relative_link(self):
        with self.skill.open('a') as stream:
            stream.write('Use sociuu-missing and [guide](missing.md).\n')
        errors = validate(self.root, [])
        self.assertTrue(any('unresolved package name sociuu-missing' in e for e in errors))
        self.assertTrue(any('broken relative link missing.md' in e for e in errors))

    def test_rejects_wrong_skill_identity(self):
        self.skill.write_text('---\nname: wrong\ndescription: Example\n---\n')
        self.assertTrue(any('mismatched skill name' in e for e in validate(self.root, [])))

    def test_rejects_absolute_link_even_when_it_exists(self):
        target = self.root / 'docs/delivery-contract.md'
        (self.root / 'README.md').write_text(f'[contract]({target})\n')
        self.assertTrue(any('nonportable link' in e for e in validate(self.root, [])))

    def test_rejects_existing_target_outside_package(self):
        with tempfile.TemporaryDirectory(dir=self.root.parent) as directory:
            target = Path(directory) / 'outside.md'
            target.write_text('outside\n')
            relative = f'../{Path(directory).name}/outside.md'
            (self.root / 'README.md').write_text(f'[outside]({relative})\n')
            self.assertTrue(any('nonportable link' in e for e in validate(self.root, [])))

    def test_rejects_missing_and_stale_distribution(self):
        repository = self.root / 'consumer'
        self.assertTrue(validate(self.root, [repository]))
        target = repository / 'docs/agents/sociuu-delivery.md'
        target.parent.mkdir(parents=True)
        target.write_text('old contract\n')
        self.assertTrue(any('drifted' in e for e in validate(self.root, [repository])))


if __name__ == '__main__':
    unittest.main()
