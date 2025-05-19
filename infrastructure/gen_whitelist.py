#!/usr/bin/env python3

"""
Generates a whitelist.txt file using a regex pattern that is applied to the target filetree
"""

import argparse
import re
from pathlib import Path


def gen_whitelist(targetdir: str, pattern: str, outputfile: str):

    targetdir  = Path(targetdir)
    outputfile = Path(outputfile)
    inputitems = [item.relative_to(targetdir).as_posix() for item in targetdir.rglob('*') if re.fullmatch(pattern, str(item.relative_to(targetdir)))]
    if whitelist := '\n'.join(inputitems):
        print(f"Found {len(inputitems)} matches:\n{whitelist}")
        outputfile.parent.mkdir(parents=True, exist_ok=True)
        outputfile.write_text(whitelist)
    else:
        print(f"WARNING: No whitelist files found in {targetdir} using '{pattern}'")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog='examples:\n'
                                            "  gen_whitelist.py targetdir 'participants.tsv'\n"
                                            "  gen_whitelist.py targetdir '.*\.(tsv|json)' ../data_user/whitelist.txt\n ")
    parser.add_argument('targetdir', help='The input directory with the full data')
    parser.add_argument('pattern', help='A fullmatch regular expression pattern that is matched against the relative path of the input data. Filepaths that match are written to the outputfile')
    parser.add_argument('outputfile', help='The output/whitelist file with the matching entries', default='whitelist.txt', nargs='?')

    # Parse the input arguments
    args = parser.parse_args()

    # Execute the main function
    gen_whitelist(**vars(args))
