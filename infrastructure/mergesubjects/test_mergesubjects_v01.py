import sys, pytest, mergesubjects
from pathlib import Path

test_path = Path('tests')
test_dirs = [d for d in test_path.iterdir() if d.is_dir() and d.name.startswith('test')]

@pytest.mark.parametrize('test_dir', test_dirs)
def test_mergesubjects(test_dir, tmp_path):

    sys.argv = ['mergesubjects', 'exe'] + [str(test_dir / f'singlesubject-{i}') for i in range(1, 4)] + [str(tmp_path / f'{test_dir.name}-merged')]
    mergesubjects.main()

if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s'])
