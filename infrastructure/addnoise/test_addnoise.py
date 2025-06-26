import os
import pytest
import tempfile
from pathlib import Path
from addnoise import addnoise

test_path = Path('tests')
test_dirs = [d for d in test_path.iterdir() if d.is_dir() and d.name.startswith('test')]

for input_dir in test_dirs:
    output_dir = tempfile.TemporaryDirectory(delete=True)
    addnoise(input_dir, output_dir.name, os.path.join(input_dir, 'whitelist.txt'), os.path.join(input_dir, 'noise.tsv'))
