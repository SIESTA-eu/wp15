import sys
# import pytest
from pathlib import Path
import singlesubject

# it is assumed to run within the infrastructure/singlesubject folder
test_path = Path('tests')

def test1(tmp_path):
    singlesubject.main(['exe', test_path / 'test1', tmp_path / 'test1/singlesubject1', 'sub-01'])
    singlesubject.main(['exe', test_path / 'test1', tmp_path / 'test1/singlesubject2', 'sub-02'])
    singlesubject.main(['exe', test_path / 'test1', tmp_path / 'test1/singlesubject3', 'sub-03'])

    # FIXME determine the correct counts and then enable these tests
    #assert len(list(tmp_path.iterdir()))                               == 9       # 6 subjects + derivatives + README + participants.tsv
    #assert len(list(tmp_path.rglob('sub-*')))                          == 3       # 6 subjects
    #assert len(list(tmp_path.rglob('*.nii')))                          == 3 * 6   # 6 subjects in root + 6 subjects in each of the 2 derivatives
    #assert len(list((tmp_path/'derivatives').iterdir()))               == 2       # 2 derivatives
    #assert len(list((tmp_path/'derivatives'/'deriv-1').iterdir()))     == 8       # 6 subjects + README + participants.tsv
    #assert len(list((tmp_path/'derivatives'/'deriv-1').glob('sub-*'))) == 6       # 6 subjects

def test2(tmp_path):
    singlesubject.main(['exe', test_path / 'test2', tmp_path / 'test2/singlesubject1', 'sub-01'])
    singlesubject.main(['exe', test_path / 'test2', tmp_path / 'test2/singlesubject2', 'sub-02'])
    singlesubject.main(['exe', test_path / 'test2', tmp_path / 'test2/singlesubject3', 'sub-03'])

    # FIXME add some tests that are not yet in test1, no reason to repeat the same tests

def test3(tmp_path):
    singlesubject.main(['exe', test_path / 'test3', tmp_path / 'test3/singlesubject1', 'sub-01'])
    singlesubject.main(['exe', test_path / 'test3', tmp_path / 'test3/singlesubject2', 'sub-02'])
    singlesubject.main(['exe', test_path / 'test3', tmp_path / 'test3/singlesubject3', 'sub-03'])

    # FIXME add some tests that are not yet in test1 and test2, no reason to repeat the same tests


if __name__ == "__main__":
    # This would run it with pytest, similar to running pytest from a GitHub action
    # pytest.main([__file__, '-v', '-s'])

    # This allows running the script directly from the console, but you need to pass the output directory as an argument.
    # The advantage of this is that you can inspect the output more easily.
    if len(sys.argv) < 2:
        print("Usage: test_singlesubject.py <outputdir>")
        sys.exit(1)
    test1(Path(sys.argv[1]))
    test2(Path(sys.argv[1]))
    test3(Path(sys.argv[1]))
