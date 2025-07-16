#!/usr/bin/env python3

import os
import pytest
import tempfile
from pathlib import Path
import calibratenoise


def test_calibratenoise():
    """
    This test estimates the noise from the LOO estimates.
    It checks if the output file is created.
    """

    test_path = Path('tests')
    test_files = [f for f in test_path.iterdir() if f.is_file() and f.name.startswith('test')]
    for input_file in test_files:
        print('-' * 80)
        print(f"Testing calibratenoise on: {input_file}")
        output_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.tsv')

        args = [
            'exe',
            input_file,
            output_file.name, 
        ]

        calibratenoise.main(args)
        assert os.path.exists(output_file.name), f"Output file {output_file.name} was not created"
        

if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s'])
