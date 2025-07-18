import sys, os
import h5py
import scipy.io
import numpy as np
from more_itertools import collapse


def is_numeric_array(obj):
    return isinstance(obj, np.ndarray) and np.issubdtype(obj.dtype, np.number)


def is_mat_struct(obj):
    return hasattr(obj, '__dict__') and not isinstance(obj, np.ndarray)


def dicts_to_list(dicts):
    result = []
    for arr in dicts.values():
        arr = np.asarray(arr)
        result.append(arr)
    return result


def extract_numeric_data(data, prefix=''):
    numeric_data = {}

    if isinstance(data, dict):
        for field, value in data.items():
            if field.startswith('__'):
                continue
            sub_prefix = f"{prefix}.{field}" if prefix else field
            numeric_data.update(extract_numeric_data(value, sub_prefix))

    elif is_mat_struct(data):
        for field, value in vars(data).items():
            sub_prefix = f"{prefix}.{field}" if prefix else field
            numeric_data.update(extract_numeric_data(value, sub_prefix))

    elif isinstance(data, np.ndarray):
        if is_numeric_array(data):
            numeric_data[prefix] = data
        elif data.dtype.names:
            # structured numpy array (e.g., MATLAB struct array)
            for i in range(data.shape[0] if data.ndim > 0 else 1):
                item = data[i] if data.ndim > 0 else data
                for field_name in data.dtype.names:
                    try:
                        value = item[field_name]
                        sub_prefix = f"{prefix}.{field_name}"
                        numeric_data.update(extract_numeric_data(value, sub_prefix))
                    except Exception:
                        continue
        else:
            # General ndarray (could be an array of structs)
            for i, item in np.ndenumerate(data):
                sub_prefix = f"{prefix}[{i}]"
                numeric_data.update(extract_numeric_data(item, sub_prefix))

    return numeric_data


def read(filepath):
    meta_keys = {'__header__', '__version__', '__globals__', '#refs#'}
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filepath} does not exist")
        
    if not os.path.isfile(filepath):
        raise ValueError(f"{filepath} is not a regular file")
        
    try:
        mat_data = scipy.io.loadmat(filepath, struct_as_record=False, squeeze_me=True, matlab_compatible=True)
    except NotImplementedError:
        with h5py.File(filepath, 'r') as file:
            mat_data = {}
            for key, dataset in file.items():
                if key == "#refs#":
                    continue
                elif isinstance(dataset, h5py.Dataset):
                    mat_data[key] = dataset[()]
                else:
                    mat_data[key] = {subkey: dataset[subkey][()] for subkey in dataset.keys()}

    structure = mat_data
    content = extract_numeric_data(mat_data)
    content = dicts_to_list(content)
    content = [float(x) for x in list(collapse(content))]
    return content, structure

def write(filepath, content, structure):
    if not os.path.exists(os.path.dirname(filepath)):
        raise FileNotFoundError(f"Directory {os.path.dirname(filepath)} does not exist")
    if not os.path.isdir(os.path.dirname(filepath)):
        raise ValueError(f"{os.path.dirname(filepath)} is not a directory")
    if not isinstance(content, list):
        raise ValueError("Content must be a list")
    if not isinstance(structure, dict):
        raise ValueError("Structure must be a dictionary")
    if not all(isinstance(x, (int, float)) for x in content):
        raise ValueError("All elements in content must be numeric (int or float)")

    # FIXME the content is not updated before writing to the file, only the structure 
    scipy.io.savemat(filepath, structure, do_compression=False, appendmat=False, format='5', long_field_names=True)
    print(f"Data written to {filepath} successfully.")
    return
