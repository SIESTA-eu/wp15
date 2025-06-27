from . import tsv

def read(filepath, delimiter=','):
    content, structure = tsv.read(filepath, delimiter)
    return content, structure

def write(filepath, content, structure, delimiter=','):
    tsv.write(filepath, content, structure, delimiter)
    return
