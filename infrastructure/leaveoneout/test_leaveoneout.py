import sys, pytest, leaveoneout
from pathlib import Path

test_path = Path('tests')
test_dirs = [d for d in test_path.iterdir() if d.is_dir() and d.name.startswith('test')]

@pytest.mark.parametrize('test_dir', test_dirs)
def test_leaveoneout(test_dir, tmp_path):
    subject_numbers = ['1', '2', '3']

    for subject in subject_numbers:
        leaveoneout.main(['exe', str(test_dir), str(tmp_path / f'{test_dir.name}/singlesubject-{subject}'), subject])


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s'])
