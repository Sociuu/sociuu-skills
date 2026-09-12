#!/usr/bin/env python3
"""Validate package links, skill identities, and optional distributed contracts."""
import argparse
import re
from pathlib import Path


def validate(root: Path, repositories: list[Path]) -> list[str]:
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
            if not (path.parent / destination).exists():
                errors.append(f'{path}: broken relative link {target}')
        # Package dependencies; external runtime/provider names are not catalog skills.
        for name in re.findall(r'\b(sociuu-[a-z][a-z-]+)\b', text):
            if name not in names and name not in {
                'sociuu-skills', 'sociuu-delivery', 'sociuu-delivery-contract'
            }:
                errors.append(f'{path}: unresolved package name {name}')
    source = root / 'docs/delivery-contract.md'
    for repository in repositories:
        destination = repository / 'docs/agents/sociuu-delivery.md'
        if not destination.exists() or destination.read_bytes() != source.read_bytes():
            errors.append(f'{repository}: delivery contract missing or drifted')
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, action='append', default=[])
    args = parser.parse_args()
    errors = validate(Path(__file__).resolve().parents[1], args.repository)
    if errors:
        print('\n'.join(errors))
        return 1
    print(f'Catalog valid; {len(args.repository)} distributed contracts checked.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
