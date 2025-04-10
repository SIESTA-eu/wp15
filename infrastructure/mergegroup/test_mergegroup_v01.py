import pytest, mergegroup
from pathlib import Path

test_path = Path('tests')
test_dirs = [d for d in test_path.iterdir() if d.is_dir() and d.name.startswith('test')]

test_cases = []
for test_dir in test_dirs:
    whitelists = sorted(test_dir.glob('whitelist*.txt'))
    for whitelist in whitelists:
        test_cases.append((test_dir, whitelist))

@pytest.mark.parametrize('test_dir, whitelist_file', test_cases)
def test_mergegroup(test_dir, whitelist_file, tmp_path):
    args = [
        'exe',
        test_dir / 'group-1',
        test_dir / 'group-2',
        test_dir / 'group-3',
        tmp_path / f'{test_dir.name}-{whitelist_file.stem}-merged',
        whitelist_file
    ]

    mergegroup.main(args)

if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s'])

