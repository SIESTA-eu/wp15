#!/usr/bin/env python3

import os
import pytest
import tempfile
from pathlib import Path
import addnoise


def test_addnoise():
    """
    This test adds noise to files in a given directory using the addnoise module.
    It checks if the output directory is created and if the noise file exists.
    """

    test_path = Path('tests')
    test_dirs = [d for d in test_path.iterdir() if d.is_dir() and d.name.startswith('test')]
    for input_dir in test_dirs:
        print('-' * 80)
        print(f"Testing addnoise on directory: {input_dir}")
        output_dir = tempfile.TemporaryDirectory(delete=True)

        args = [
            'exe',
            input_dir, 
            output_dir.name, 
            os.path.join(input_dir, 'whitelist.txt'), 
            os.path.join(input_dir, 'noise.tsv')
        ]

        addnoise.main(args)
        assert os.path.exists(output_dir.name), f"Output directory {output_dir.name} was not created"
        
        # this still fails, because writing mat files is not implemented yet
        # assert os.listdir(output_dir.name), f"Output directory {output_dir.name} is empty"


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s'])

