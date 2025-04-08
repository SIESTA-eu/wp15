import sys
# import pytest
from pathlib import Path
import mergegroup

# it is assumed to run within the infrastructure/mergegroup folder
test_path = Path('tests')

def test0(tmp_path):
    prefix = test_path / 'test0'
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test0-merged', prefix / 'whitelist.txt'])

def test1(tmp_path):
    prefix = test_path / 'test1'
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test1A-merged', prefix / 'whitelistA.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test1B-merged', prefix / 'whitelistB.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test1C-merged', prefix / 'whitelistC.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test1D-merged', prefix / 'whitelistD.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test1E-merged', prefix / 'whitelistE.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test1F-merged', prefix / 'whitelistF.txt'])

def test2(tmp_path):
    prefix = test_path / 'test2'
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test2A-merged', prefix / 'whitelistA.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test2B-merged', prefix / 'whitelistB.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test2C-merged', prefix / 'whitelistC.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test2D-merged', prefix / 'whitelistD.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test2E-merged', prefix / 'whitelistE.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test2F-merged', prefix / 'whitelistF.txt'])

def test3(tmp_path):
    prefix = test_path / 'test3'
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test3A-merged', prefix / 'whitelistA.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test3B-merged', prefix / 'whitelistB.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test3C-merged', prefix / 'whitelistC.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test3D-merged', prefix / 'whitelistD.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test3E-merged', prefix / 'whitelistE.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test3F-merged', prefix / 'whitelistF.txt'])

def test4(tmp_path):
    prefix = test_path / 'test4'
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test4A-merged', prefix / 'whitelistA.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test4B-merged', prefix / 'whitelistB.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test4C-merged', prefix / 'whitelistC.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test4D-merged', prefix / 'whitelistD.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test4E-merged', prefix / 'whitelistE.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test4F-merged', prefix / 'whitelistF.txt'])

def test5(tmp_path):
    prefix = test_path / 'test5'
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test5A-merged', prefix / 'whitelistA.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test5B-merged', prefix / 'whitelistB.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test5C-merged', prefix / 'whitelistC.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test5D-merged', prefix / 'whitelistD.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test5E-merged', prefix / 'whitelistE.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test5F-merged', prefix / 'whitelistF.txt'])

def test6(tmp_path):
    prefix = test_path / 'test6'
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test6A-merged', prefix / 'whitelistA.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test6B-merged', prefix / 'whitelistB.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test6C-merged', prefix / 'whitelistC.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test6D-merged', prefix / 'whitelistD.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test6E-merged', prefix / 'whitelistE.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test6F-merged', prefix / 'whitelistF.txt'])

def test7(tmp_path):
    prefix = test_path / 'test7'
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test7A-merged', prefix / 'whitelistA.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test7B-merged', prefix / 'whitelistB.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test7C-merged', prefix / 'whitelistC.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test7D-merged', prefix / 'whitelistD.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test7E-merged', prefix / 'whitelistE.txt'])
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test7F-merged', prefix / 'whitelistF.txt'])

def test8(tmp_path):
    prefix = test_path / 'test8'
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test8-merged', prefix / 'whitelist.txt'])

def test9(tmp_path):
    prefix = test_path / 'test9'
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test9-merged', prefix / 'whitelist.txt'])

def test10(tmp_path):
    prefix = test_path / 'test10'
    mergegroup.main(['exe', prefix / 'group-1', prefix / 'group-2', prefix / 'group-3', tmp_path / 'test10-merged', prefix / 'whitelist.txt'])


if __name__ == "__main__":
    # This would run it with pytest, similar to running pytest from a GitHub action
    # pytest.main([__file__, '-v', '-s'])

    # This allows running the script directly from the console, but you need to pass the output directory as an argument.
    # The advantage of this is that you can inspect the output more easily.
    if len(sys.argv) < 2:
        print("Usage: test_mergegroup.py <outputdir>")
        sys.exit(1)
    test0(Path(sys.argv[1]))
    test1(Path(sys.argv[1]))
    test2(Path(sys.argv[1]))
    test3(Path(sys.argv[1]))
    test4(Path(sys.argv[1]))
    test5(Path(sys.argv[1]))
    test6(Path(sys.argv[1]))
    test7(Path(sys.argv[1]))
    test8(Path(sys.argv[1]))
    test9(Path(sys.argv[1]))
    test10(Path(sys.argv[1]))
