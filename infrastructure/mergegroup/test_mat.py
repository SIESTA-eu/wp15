import os
from lib import mat

# This test script goes over a number of different MATLAB .mat files 
# with differences in the version (v4, v6, v7, v73) and differences
# in their content (array, struct, cell)

basename = 'tests/test11'
for filename in os.listdir(basename):
    if not filename.endswith('.mat'):
        continue
    print('_' * 80)
    filename = os.path.join(basename, filename)
    content, structure = mat.read(filename)
    print(f"Content   for {filename}: {content}")
    print(f"Structure for {filename}: {structure}") 
