import sys, pytest, mergesubjects
from pathlib import Path

# it is assumed to run within the infrastructure/mergegroup folder
test_path = Path('tests')

def test1(tmp_path):
    prefix = test_path / 'test1'
    sys.argv = ['mergesubjects', 'exe', str(prefix / 'singlesubject-1'), 
                                        str(prefix / 'singlesubject-2'), 
                                        str(prefix / 'singlesubject-3'), 
                                        str(tmp_path / 'test1-merged')]
    mergesubjects.main()

def test2(tmp_path):
    prefix = test_path / 'test2'
    sys.argv = ['mergesubjects', 'exe', str(prefix / 'singlesubject-1'), 
                                        str(prefix / 'singlesubject-2'), 
                                        str(prefix / 'singlesubject-3'),
                                        str(tmp_path / 'test2-merged')]
    mergesubjects.main()

def test3(tmp_path):
    prefix = test_path / 'test3'
    sys.argv = ['mergesubjects', 'exe', str(prefix / 'singlesubject-1'), 
                                        str(prefix / 'singlesubject-2'), 
                                        str(prefix / 'singlesubject-3'), 
                                        str(tmp_path / 'test3-merged')]
    mergesubjects.main()    
if __name__ == "__main__":
    # This would run it with pytest, similar to running pytest from a GitHub action
    pytest.main([__file__, '-v', '-s'])

    # This allows running the script directly from the console, but you need to pass the output directory as an argument.
    # The advantage of this is that you can inspect the output more easily.
    """
    if len(sys.argv) < 2:
        print("Usage: test_mergesubjects.py <outputdir>")
        sys.exit(1)
    test1(Path(sys.argv[1]))
    test2(Path(sys.argv[1]))
    test3(Path(sys.argv[1]))
    """
