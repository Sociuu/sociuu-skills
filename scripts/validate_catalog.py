#!/usr/bin/env python3
"""Validate package links and skill identities."""
import argparse
import re
from pathlib import Path


def validate(root: Path) -> list[str]:
    errors = []
    skills = root / 'skills'
    names = {p.parent.name for p in skills.glob('*/SKILL.md')}
    documents = [root / 'README.md', *skills.rglob('*.md'), *root.glob('docs/*.md')]
    for path in documents:
        text = path.read_text()
        if path.name == 'SKILL.md':
            match = re.match(r'\A---\n(.*?)\n---\n', text, re.S)
            header = match.group(1) if match else ''
            if not re.search(r'^name: ' + re.escape(path.parent.name) + r'$', header, re.M):
                errors.append(f'{path}: missing or mismatched skill name')
            if not re.search(r'^description: .+', header, re.M):
                errors.append(f'{path}: missing description')
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            if '://' in target or target.startswith('#'):
                continue
            destination = target.split('#', 1)[0]
            resolved = (path.parent / destination).resolve()
            if Path(destination).is_absolute() or not resolved.is_relative_to(root.resolve()):
                errors.append(f'{path}: nonportable link {target}')
            elif not resolved.exists():
                errors.append(f'{path}: broken relative link {target}')
        # Package dependencies; external runtime/provider names are not catalog skills.
        for name in re.findall(r'\b(sociuu-[a-z][a-z-]+)\b', text):
            if name not in names and name != 'sociuu-skills':
                errors.append(f'{path}: unresolved package name {name}')
    return sorted(set(errors))


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    errors = validate(Path(__file__).resolve().parents[1])
    if errors:
        print('\n'.join(errors))
        return 1
    print('Catalog valid.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
