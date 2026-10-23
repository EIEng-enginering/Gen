"""Fail fast if the approved project register is incomplete or special choices drift."""
import json
from pathlib import Path


def validate(path: Path) -> None:
    data = json.loads(path.read_text(encoding='utf-8'))
    decisions = data['decisions']
    assert data['count'] == len(decisions) == 50
    assert [item['id'] for item in decisions] == [f'Q{i:02d}' for i in range(1, 51)]
    mapping = {item['id']: item['selection'] for item in decisions}
    assert mapping['Q12'] == 'A+B'
    assert mapping['Q14'] == 'B'
    assert mapping['Q19'] == 'A+B+C'
    assert all(item['requirement'] and item['verification'] for item in decisions)


if __name__ == '__main__':
    project_root = Path(__file__).resolve().parent.parent
    validate(project_root / 'docs' / 'DECISIONS_Q01_Q50.json')
    print('PASS: all 50 approved decisions match Rev A baseline')
