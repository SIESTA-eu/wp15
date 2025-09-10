import nibabel as nib
import os, mne, re
from collections import defaultdict

class fetch_files:
    def __init__(self, path):
        self.path = path

    def sort_keys(self, folder_name):
        match = re.match(r'sub-(\d+)', folder_name)
        if match:
            return (0, int(match.group(1)))
        elif folder_name == "sub-emptyroom":
            return (1, float('inf') - 1)
        elif folder_name == "derivatives":
            return (1, float('inf'))
        return (1, float('inf') + 1)

    def collect_(self, pattern, category_func=None):
        ff = defaultdict(list)
        compiled_pattern = re.compile(pattern)

        for root, _, files in os.walk(self.path):
            if ".git" in root:
                continue
            for file in files:
                full_path = os.path.join(root, file)
                if compiled_pattern.match(file):
                    category = category_func(root) if category_func else ""
                    rel_folder = os.path.relpath(root, self.path).split(os.sep)[0]
                    key = (category, rel_folder)
                    ff[key].append(full_path)

        return ff

    def fif_(self):
        def extract_(filename):
            match = re.search(r'_run-(\d+)_meg\.fif$', filename)
            return int(match.group(1)) if match else float('inf')

        ff = self.collect_(
            pattern=r'sub-\d+_ses-[^_]+_task-[^_]+_run-\d+_meg\.fif$',
            category_func=None
        )

        sorted_files = []
        for (_, folder), files in sorted(ff.items(), key=lambda x: self.sort_keys(x[0][1])):
            files.sort(key=lambda f: extract_(os.path.basename(f)))
            sorted_files.extend(files)

        return sorted_files

    def vhdr_(self):
        def extract_(filename):
            match = re.search(r'sub-(\d+)', filename)
            return int(match.group(1)) if match else float('inf')

        ff = self.collect_(
            pattern=r'sub-\d+_ses-[^_]+_task-[^_]+_eeg\.vhdr$',
            category_func=None)

        sorted_files = []
        for (_, folder), files in sorted(ff.items(), key=lambda x: self.sort_keys(x[0][1])):
            #files.sort(key=lambda f: extract_(os.path.basename(f)))
            sorted_files.extend(sorted(files))

        return sorted_files

    def nii_(self):
        def category_(path):
            if "func" in path:
                return "func"
            elif "anat" in path:
                return "anat"
            return None

        ff = self.collect_(
            pattern=r'.*\.(nii(\.gz)?)$',
            category_func=category_
        )

        sorted_files = []
        for category in ["func", "anat"]:
            category_folders = {
                key: val for key, val in ff.items() if key[0] == category
            }
            for (test, folder), files in sorted(category_folders.items(), key=lambda x: self.sort_keys(x[0][1])):
                sorted_files.extend(sorted(files))  

        return sorted_files

class neuro_reader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.raw = None
        self.data = None
        self.sfreq = None
        self.channel_names = None
        self.times = None
        self.file_type = None

        self._load_file()
        self._extract_metadata()

    def _load_file(self):
        mne.set_log_level('WARNING')
        ext = os.path.splitext(self.file_path)[1].lower()

        if ext == '.fif':
            self.file_type = 'fif'
            self.raw = mne.io.read_raw_fif(self.file_path, preload=True)
        elif ext == '.vhdr':
            self.file_type = 'vhdr'
            self.raw = mne.io.read_raw_brainvision(self.file_path, preload=True)
        elif ext == '.set':
            self.file_type = 'set'
            self.raw = mne.io.read_raw_eeglab(self.file_path, preload=True)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        self.data = self.raw.get_data()

    def _extract_metadata(self):
        if self.raw is None:
            return

        self.sfreq = self.raw.info['sfreq']  
        self.channel_names = self.raw.info['ch_names']
        self.times = self.raw.times  

    def get_data(self):
        return self.data

    def get_sampling_frequency(self):
        return self.sfreq

    def get_channel_names(self):
        return self.channel_names

    def get_times(self):
        return self.times

    def get_file_type(self):
        return self.file_type


class nii_reader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.img = None
        self.data = None
        self.orientation = None
        self.dim_orientations = None         
        self.load_nii()
        self._nii_determine_orientation()

    def load_nii(self):
        self.img = nib.load(self.file_path)
        self.data = self.img.get_fdata()
    
    def _nii_determine_orientation(self):
        if self.img is None:
            return
        
        ras_affine = nib.orientations.io_orientation(self.img.affine)
        orientation_codes = nib.orientations.ornt2axcodes(ras_affine)
        
        self.dim_orientations = orientation_codes
        self.orientation = self._interpret_primary_orientation(orientation_codes)
    
    def _interpret_primary_orientation(self, codes):
        if 'S' in codes[2]: 
            return "axial"
        elif 'A' in codes[2]:  
            return "coronal"
        elif 'L' in codes[2] or 'R' in codes[2]:  
            return "sagittal"
        else:
            return "unknown"
    
    def get_data(self):
        return self.data
    
    def get_orientation(self):
        return self.orientation
    
    def get_dimension_orientations(self):
        return self.dim_orientations

