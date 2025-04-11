import sys, pytest, singlesubject
from pathlib import Path

test_path = Path('tests')
test_dirs = [d for d in test_path.iterdir() if d.is_dir() and d.name.startswith('test')]

@pytest.mark.parametrize('test_dir', test_dirs)
def test_singlesubject(test_dir, tmp_path):
    subject_numbers = ['1', '2', '3']
    # "Usage: singlesubject.py <inputdir> <outputdir> <participant_nr>"
    for participant_nr in subject_numbers:
        print()
        singlesubject.main(['exe', str(test_dir), str(tmp_path / f'{test_dir.name}/singlesubject-output-{participant_nr}'), participant_nr])


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s'])
