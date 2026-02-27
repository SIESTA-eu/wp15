#!/usr/bin/env python3

import sys, os
import pytest
from pathlib import Path
import tempfile
import mergegroup
from lib import mat, csv, tsv


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


def test_tsv_readwrite():
    """
    This test reads a TSV file, writes it back to a new file,
    and then reads the new file to ensure the content and structure match.
    """
    tsv_heading_input = 'tests/test12/headings.tsv'
    tsv_heading_output = tempfile.NamedTemporaryFile(delete=False).name
    [content1, structure1] = tsv.read(tsv_heading_input)
    tsv.write(tsv_heading_output, content1, structure1)
    [content2, structure2] = tsv.read(tsv_heading_output)
    os.remove(tsv_heading_output)
    assert content1 == content2, "TSV content mismatch after writing and reading"
    assert structure1 == structure2, "TSV structure mismatch after writing and reading"


def test_csv_readwrite():
    """
    This test reads a CSV file, writes it back to a new file,
    and then reads the new file to ensure the content and structure match.
    """
    csv_heading_input = 'tests/test12/headings.csv'
    csv_heading_output = tempfile.NamedTemporaryFile(delete=False).name
    [content1, structure1] = csv.read(csv_heading_input)
    csv.write(csv_heading_output, content1, structure1)
    [content2, structure2] = csv.read(csv_heading_output)
    os.remove(csv_heading_output)
    assert content1 == content2, "CSV content mismatch after writing and reading"
    assert structure1 == structure2, "CSV structure mismatch after writing and reading"


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s'])

