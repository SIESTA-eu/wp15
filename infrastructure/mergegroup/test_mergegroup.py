#!/usr/bin/env python3

import os
import pytest
from pathlib import Path
import mergegroup
from lib import mat

test_path = Path('tests')
test_dirs = [d for d in test_path.iterdir() if d.is_dir() and d.name.startswith('test')]

test_cases = []
for test_dir in test_dirs:
    whitelists = sorted(test_dir.glob('whitelist*.txt'))
    for whitelist in whitelists:
        test_cases.append((test_dir, whitelist))


@pytest.mark.parametrize('test_dir, whitelist_file', test_cases)
def test_mergegroup(test_dir, whitelist_file, tmp_path):
    """
    This test merges multiple groups of files into a single group
    using the mergegroup module. It checks if the merged file exists
    and counts the number of lines in the merged file.
    """
    args = [
        'exe',
        test_dir / 'group-1',
        test_dir / 'group-2',
        test_dir / 'group-3',
        tmp_path / f'{test_dir.name}-{whitelist_file.stem}',
        whitelist_file
    ]
    mergegroup.main(args)
    
    merged_file = tmp_path / f'{test_dir.name}-{whitelist_file.stem}' / 'group-merged.tsv'
    assert merged_file.exists(), f"Merged file not found: {merged_file}"
    
    num_lines = sum(1 for _ in merged_file.open('r', encoding='utf-8'))
    print(f"Line count for {merged_file}: {num_lines}")


def test_mat():
    """
    This test goes over a number of different MATLAB .mat files 
    with differences in the version (v4, v6, v7, v73) and differences
    in their content (array, struct, cell)
    """

    basename = 'tests/test11'
    for filename in os.listdir(basename):
        if not filename.endswith('.mat'):
            continue
        print('_' * 80)
        filename = os.path.join(basename, filename)
        content, structure = mat.read(filename)
        print(f"Content   for {filename}: {content}")
        print(f"Structure for {filename}: {structure}") 


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s'])

