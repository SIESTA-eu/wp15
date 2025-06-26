import os
from lib import mat

basename = 'tests/test11'
for filename in os.listdir(basename):
    if not filename.endswith('.mat'):
        continue
    print('_' * 80)
    filename = os.path.join(basename, filename)
    content, structure = mat.read(filename)
    print(f"Content   for {filename}: {content}")
    print(f"Structure for {filename}: {structure}") 
