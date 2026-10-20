"""Read-only live GitHub governance report; no metadata writes or token output."""
import argparse
import json
from pathlib import Path
import subprocess


def audit(taxonomy, labels, issues):
    errors = []
    actual = {label['name']: label for label in labels}
    expected = {label['name']: label for label in taxonomy['labels']}
    for name, label in expected.items():
        found = actual.get(name)
        if (not found or found['color'].lower() != label['color'].lower()
                or found.get('description') != label['description']):
            errors.append('label definition drift: ' + name)
    for issue in issues:
        if issue['state'] != 'open':
            continue  # Historical inventory is counted, never rewritten.
        names = {label['name'] for label in issue['labels']}
        priorities = {n for n in names if n.startswith('priority:')}
        if len(priorities) != 1 or not priorities <= set(taxonomy['priority_order']):
            errors.append(f"#{issue['number']}: require exactly one canonical priority")
        for prefix in ('type:', 'area:'):
            if not any(n.startswith(prefix) for n in names):
                errors.append(f"#{issue['number']}: missing {prefix} classification")
        for name in names:
            if name.startswith(('type:', 'area:', 'stage:')) and name not in expected:
                errors.append(f"#{issue['number']}: undocumented taxonomy extension {name}")
    return errors


def get(repo, resource):
    result = subprocess.run(
        ['gh', 'api', '--method', 'GET', '--paginate', '--slurp',
         f'repos/{repo}/{resource}'], check=True, capture_output=True, text=True)
    return [item for page in json.loads(result.stdout) for item in page]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, help='OWNER/REPO (authenticated read access)')
    parser.add_argument('--taxonomy', type=Path,
                        default=Path(__file__).resolve().parents[1] / '.github/labels.json')
    args = parser.parse_args()
    taxonomy = json.loads(args.taxonomy.read_text())
    try:
        labels = get(args.repo, 'labels?per_page=100')
        issues = get(args.repo, 'issues?state=all&per_page=100')
        milestones = get(args.repo, 'milestones?state=all&per_page=100')
    except subprocess.CalledProcessError:
        parser.exit(2, 'BLOCKED: GitHub metadata GET failed; check read access.\n')
    errors = audit(taxonomy, labels, issues)
    print(f'{args.repo}: {len(issues)} Issues/PRs, {len(labels)} labels, '
          f'{len(milestones)} milestones (all states)')
    for issue in issues:
        if issue['state'] == 'open':
            milestone = issue.get('milestone')
            print(f"#{issue['number']}: " + ', '.join(l['name'] for l in issue['labels'])
                  + '; milestone=' + (milestone['title'] if milestone else 'none (review applicability)'))
    print('\n'.join(errors) if errors else 'PASS: definitions and active classification; review stage/milestone applicability against roadmap')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
