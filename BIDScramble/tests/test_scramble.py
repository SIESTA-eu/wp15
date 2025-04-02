import json
import shutil
import numpy as np
import pandas as pd
import math
import mne
import brainvision
import nibabel as nib
import urllib.request, urllib.error
from bidscramble import __version__, __description__, __url__
from bidscramble.scramble_stub import scramble_stub
from bidscramble.scramble_tsv import scramble_tsv
from bidscramble.scramble_json import scramble_json
from bidscramble.scramble_nii import scramble_nii
from bidscramble.scramble_fif import scramble_fif
from bidscramble.scramble_brainvision import scramble_brainvision
from bidscramble.scramble_swap import scramble_swap
from bidscramble.scramble_pseudo import scramble_pseudo


def test_scramble_stub(tmp_path):

    # Create the input data
    (tmp_path/'input'/'code').mkdir(parents=True)
    (tmp_path/'input'/'derivatives').mkdir()
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004148/participants.tsv', tmp_path/'input'/'participants.tsv')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004148/participants.json', tmp_path/'input'/'participants.json')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004148/dataset_description.json', tmp_path/'input'/'dataset_description.json')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004148/README', tmp_path/'input'/'README')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004148/CHANGES', tmp_path/'input'/'CHANGES')

    # Fix the spdx identifier
    description = (tmp_path/'input'/'dataset_description.json').read_text().replace('CC0', 'CC0-1.0')
    (tmp_path/'input'/'dataset_description.json').write_text(description)

    # Create the output data
    scramble_stub(tmp_path/'input', tmp_path/'output', '(?!.*derivatives(/|$)).*', False)

    # Check that all output data - `derivatives` + `LICENSE` is there
    assert (tmp_path/'output'/'LICENSE').is_file()
    assert (tmp_path/'output'/'code').is_dir()
    assert not (tmp_path/'output'/'derivatives').exists()
    assert len(list((tmp_path/'input').rglob('*'))) == len(list((tmp_path/'output').rglob('*')))

    # Check that the 'GeneratedBy' and 'DatasetType' have been written
    with (tmp_path/'output'/'dataset_description.json').open('r') as fid:
        description = json.load(fid)
    assert description['GeneratedBy'] == [{'Name':'BIDScramble', 'Version':__version__, 'Description:':__description__, 'CodeURL':__url__}]
    assert description['DatasetType'] == 'derivative'

    # Check that the README file has been copied
    readme = (tmp_path/'output'/'README').read_text()
    assert 'EEG' in readme


def test_scramble_tsv(tmp_path):

    # Create the input data
    (tmp_path/'input').mkdir()
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004148/participants.tsv',  tmp_path/'input'/'participants.tsv')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004148/participants.json', tmp_path/'input'/'test.tsv')

    # Fix the space and "n/a " values
    tsvdata = (tmp_path/'input'/'participants.tsv').read_text().replace('\tn/a ', '\tn/a').replace('\t ', '\tn/a')
    (tmp_path/'input'/'participants.tsv').write_text(tsvdata)
    (tmp_path/'input'/'partici_test.tsv').write_text(tsvdata)

    # Create nulled output data
    scramble_tsv(tmp_path/'input', tmp_path/'output', 'partici.*\\.tsv', False, 'null', '')
    assert (tmp_path/'output'/'partici_test.tsv').is_file()
    assert not (tmp_path/'output'/'test.tsv').exists()

    # Check that the participants.tsv data is properly nulled
    inputdata  = pd.read_csv(tmp_path/'input'/'participants.tsv', sep='\t')
    outputdata = pd.read_csv(tmp_path/'output'/'participants.tsv', sep='\t')
    assert inputdata.shape == outputdata.shape
    for column, values in outputdata.items():
        assert column in inputdata.columns
        assert values.isnull().all()

    # Create permuted output data
    (tmp_path/'output'/'participants.tsv').unlink()
    scramble_tsv(tmp_path/'input', tmp_path/'output', 'partici.*\\.tsv', False, 'permute', '(Height|Weig.*)')

    # Check that the participants.tsv data is properly permuted
    outputdata = pd.read_csv(tmp_path/'output'/'participants.tsv', sep='\t')
    assert inputdata.shape == outputdata.shape
    assert not inputdata['participant_id'].equals(outputdata['participant_id'])
    for key in ['Height', 'Weight', 'age']:
        assert not inputdata[key].equals(outputdata[key])
        assert math.isclose(inputdata[key].mean(), outputdata[key].mean())
        assert math.isclose(inputdata[key].std(),  outputdata[key].std())

    # Check that the relation between 'Height' and 'Weight' is preserved, but not between 'SAS_1stVisit' and 'SAS_2ndVisit'
    assert math.isclose(inputdata['Height'].corr(inputdata['Weight']), outputdata['Height'].corr(outputdata['Weight']))
    assert not math.isclose(inputdata['SAS_1stVisit'].corr(inputdata['SAS_2ndVisit']), outputdata['SAS_1stVisit'].corr(outputdata['SAS_2ndVisit']))


def test_scramble_json(tmp_path):

    # Create the input data
    eegjson = 'sub-01/ses-session1/eeg/sub-01_ses-session1_task-eyesclosed_eeg.json'
    (tmp_path/'input'/'sub-01'/'ses-session1'/'eeg').mkdir(parents=True)
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004148/participants.json', tmp_path/'input'/'participants.json')
    urllib.request.urlretrieve(f"https://s3.amazonaws.com/openneuro.org/ds004148/{eegjson}", tmp_path/'input'/eegjson)

    # Create the output data
    scramble_json(tmp_path/'input', tmp_path/'output', r'.*/sub-.*\.json', False, '(?!RecordingDuration|Channel).*')
    assert (tmp_path/'output'/eegjson).is_file()
    assert not (tmp_path/'output'/'participants.json').exists()

    # Check that the participants.json data is properly preserved/emptied
    with (tmp_path/'input'/eegjson).open('r') as fid:
        inputdata = json.load(fid)
    with (tmp_path/'output'/eegjson).open('r') as fid:
        outputdata = json.load(fid)
    assert inputdata.keys() == outputdata.keys()
    assert inputdata['TaskDescription'] == outputdata['TaskDescription']
    assert not outputdata['RecordingDuration']
    assert not outputdata['EMGChannelCount']


def test_scramble_nii(tmp_path):

    # Create the input data
    niifile = 'sub-01/ses-mri/dwi/sub-01_ses-mri_dwi.nii.gz'
    (tmp_path/'input'/'sub-01'/'ses-mri'/'dwi').mkdir(parents=True)
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds000117/participants.tsv', tmp_path/'input'/'participants.tsv')
    urllib.request.urlretrieve(f"https://s3.amazonaws.com/openneuro.org/ds000117/{niifile}", tmp_path/'input'/niifile)

    # Create nulled output data
    scramble_nii(tmp_path/'input', tmp_path/'output', 'sub.*\\.nii.gz', False, 'null')
    assert (tmp_path/'output'/niifile).is_file()
    assert not (tmp_path/'output'/'participants.tsv').exists()

    # Check that the NIfTI data is properly nulled
    outdata = nib.load(tmp_path/'output'/niifile).get_fdata()
    assert outdata.shape == (96, 96, 68, 65)
    assert outdata.sum() == 0

    # Create blurred output data
    (tmp_path/'output'/niifile).unlink()
    scramble_nii(tmp_path/'input', tmp_path/'output', 'sub.*\\.nii.gz', False, 'blur', fwhm=12)
    assert (tmp_path/'output'/niifile).is_file()

    # Check that the NIfTI data is properly blurred
    indata  = nib.load(tmp_path/'input'/niifile).get_fdata()
    outdata = nib.load(tmp_path/'output'/niifile).get_fdata()
    assert outdata.shape == (96, 96, 68, 65)
    assert outdata.sum() > 1000000
    assert outdata.sum() - indata.sum() < 1
    assert np.abs(outdata - indata).sum() > 1000

    # Create permuted output data
    (tmp_path/'output'/niifile).unlink()
    scramble_nii(tmp_path/'input', tmp_path/'output', 'sub.*\\.nii.gz', False, 'permute', dims=['x', 'z'], independent=False)
    assert (tmp_path/'output'/niifile).is_file()

    # Check that the NIfTI data is properly permuted
    outdata = nib.load(tmp_path/'output'/niifile).get_fdata()
    assert outdata.shape == (96, 96, 68, 65)
    assert outdata.sum() > 1000000
    assert outdata.sum() - indata.sum() < 1
    assert np.abs(outdata - indata).sum() > 1000

    # Create independently permuted output data
    (tmp_path/'output'/niifile).unlink()
    scramble_nii(tmp_path/'input', tmp_path/'output', 'sub.*\\.nii.gz', False, 'permute', dims=['x'], independent=True)
    assert (tmp_path/'output'/niifile).is_file()

    # Check that the NIfTI data is properly permuted
    outdata = nib.load(tmp_path/'output'/niifile).get_fdata()
    assert outdata.shape == (96, 96, 68, 65)
    assert outdata.sum() > 1000000
    assert outdata.sum() - indata.sum() < 1
    assert np.abs(outdata - indata).sum() > 1000

    # Create diffused output data
    (tmp_path/'output'/niifile).unlink()
    scramble_nii(tmp_path/'input', tmp_path/'output', 'sub.*\\.nii.gz', False, 'scatter', radius=25)
    assert (tmp_path/'output'/niifile).is_file()

    # Check that the NIfTI data is properly diffused
    outdata = nib.load(tmp_path/'output'/niifile).get_fdata()
    assert outdata.shape == (96, 96, 68, 65)
    assert outdata.sum() > 1000000
    assert outdata.sum() - indata.sum() < 1
    assert np.abs(outdata - indata).sum() > 1000

    # Create wobbled output data
    (tmp_path/'output'/niifile).unlink()
    scramble_nii(tmp_path/'input', tmp_path/'output', 'sub.*\\.nii.gz', False, 'wobble', amplitude=25, freqrange=[0.05, 0.5])
    assert (tmp_path/'output'/niifile).is_file()

    # Check that the NIfTI data is properly diffused
    outdata = nib.load(tmp_path/'output'/niifile).get_fdata()
    assert outdata.shape == (96, 96, 68, 65)
    assert outdata.sum() > 1000000
    assert outdata.sum() - indata.sum() < 1
    assert np.abs(outdata - indata).sum() > 1000


def test_scramble_fif(tmp_path):

    # Create the input data
    (tmp_path/'input'/'sub-01'/'ses-meg'/'meg').mkdir(parents=True)
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds000117/dataset_description.json', tmp_path/'input'/'dataset_description.json')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds000117/README', tmp_path/'input'/'README')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds000117/CHANGES', tmp_path/'input'/'CHANGES')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds000117/participants.tsv', tmp_path/'input'/'participants.tsv')
    megfile = 'sub-01/ses-meg/meg/sub-01_ses-meg_task-facerecognition_run-01_meg.fif'
    # urllib.request.urlretrieve(f"https://s3.amazonaws.com/openneuro.org/ds000117/{megfile}", tmp_path/'input'/megfile)      # = 820MB -> replace with MNE file (below)
    urllib.request.urlretrieve('https://raw.githubusercontent.com/mne-tools/mne-testing-data/refs/heads/master/MEG/sample/sample_audvis_trunc_raw.fif', tmp_path/'input'/megfile)

    # Create nulled output data
    scramble_fif(tmp_path/'input', tmp_path/'output', r'sub.*\.fif', False, 'null')
    assert (tmp_path/'output'/megfile).is_file()
    assert not (tmp_path/'output'/'participants.tsv').exists()

    # fif files come in 3 flavours that use different reader functions
    isevoked  = False
    isepoched = False
    israw     = True
    if israw:
        obj = mne.io.read_raw_fif(tmp_path/'output'/megfile, preload=True)
    elif isevoked:
        obj = mne.Evoked(tmp_path/'output'/megfile)
    elif isepoched:
        raise Exception(f"cannot read epoched FIF file: {megfile}")

    # Check that the output data is properly nulled
    data = obj.get_data()
    assert data.shape == (376, 6007)
    assert np.sum(data[99]) == 0        # check one channel in the middle of the array


def test_scramble_brainvision(tmp_path):
    # Create the input data
    (tmp_path/'input'/'sub-02'/'ses-01'/'eeg').mkdir(parents=True)
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004951/dataset_description.json', tmp_path/'input'/'dataset_description.json')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004951/README', tmp_path/'input'/'README')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004951/CHANGES', tmp_path/'input'/'CHANGES')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds004951/participants.tsv', tmp_path/'input'/'participants.tsv')
    eegfile = 'sub-02/ses-01/eeg/sub-02_ses-01_task-letters_run-01_eeg.eeg'
    # urllib.request.urlretrieve(f"https://s3.amazonaws.com/openneuro.org/ds004951/{eegfile}", tmp_path/'input'/eegfile)  # = 1.2GB -> replace with MNE files (below)
    urllib.request.urlretrieve('https://raw.githubusercontent.com/robertoostenveld/brainvision/refs/heads/main/test/test.eeg', tmp_path/'input'/eegfile)
    eegfile = 'sub-02/ses-01/eeg/sub-02_ses-01_task-letters_run-01_eeg.vmrk'
    urllib.request.urlretrieve('https://raw.githubusercontent.com/robertoostenveld/brainvision/refs/heads/main/test/test.vmrk', tmp_path/'input'/eegfile)
    data = (tmp_path/'input'/eegfile).read_text()
    (tmp_path/'input'/eegfile).write_text(data.replace('test', 'sub-02_ses-01_task-letters_run-01_eeg'))
    eegfile = 'sub-02/ses-01/eeg/sub-02_ses-01_task-letters_run-01_eeg.vhdr'
    urllib.request.urlretrieve('https://raw.githubusercontent.com/robertoostenveld/brainvision/refs/heads/main/test/test.vhdr', tmp_path/'input'/eegfile)
    data = (tmp_path/'input'/eegfile).read_text()
    (tmp_path/'input'/eegfile).write_text(data.replace('test', 'sub-02_ses-01_task-letters_run-01_eeg'))

    # Create nulled output data
    scramble_brainvision(tmp_path/'input', tmp_path/'output', r'sub.*\.vhdr', False, 'null')
    assert (tmp_path/'output'/eegfile).is_file()
    assert not (tmp_path/'output'/'participants.tsv').exists()

    # Check that the output data is properly nulled
    (vhdr, vmrk, data) = brainvision.read(tmp_path/'output'/eegfile)
    assert data.shape == (32, 7900)
    assert np.sum(data[16]) == 0        # check one channel in the middle of the array


def test_scramble_swap(tmp_path):

    def load_data(jsonfile):
        with (tmp_path/'input'/jsonfile).open('r') as fid:
            inputdata = json.load(fid)
        with (tmp_path/'output'/jsonfile).open('r') as fid:
            outputdata = json.load(fid)
        return inputdata, outputdata

    # Create the input data
    funcjsons = []
    for sub in range(1,9):
        (tmp_path/'input'/f"sub-0{sub}"/'func').mkdir(parents=True)
        for run in range(1,5):
            if not (sub == 8 and run == 4):
                funcjsons.append(f"sub-0{sub}/func/sub-0{sub}_task-closed_run-0{run}_bold.json")
                print('Downloading:', funcjsons[-1])
                urllib.request.urlretrieve(f"https://s3.amazonaws.com/openneuro.org/ds005194/{funcjsons[-1]}", tmp_path/'input'/funcjsons[-1])
    # Add 1 unique run-05 file
    funcjsons.append('sub-01/func/sub-01_task-closed_run-05_bold.json')
    urllib.request.urlretrieve(f"https://s3.amazonaws.com/openneuro.org/ds005194/{funcjsons[-1]}", tmp_path/'input'/funcjsons[-1])

    # Create the output data for swapping between subjects and runs. N.B: Run-05 swapping will sometimes fail due to random sampling, so try it multiple times
    for n in range(3):
        scramble_swap(tmp_path/'input', tmp_path/'output', r'.*/sub-.*\.json', ['subject', 'run'], False)
        for funcjson in funcjsons:
            assert (tmp_path/'output'/funcjson).is_file()
        inputdata, outputdata = load_data(funcjsons[-1])        # Get the unique run-05 data
        if inputdata['AcquisitionTime'] != outputdata['AcquisitionTime']: break

    # Check that the run-05 json data is properly swapped
    assert inputdata.keys() == outputdata.keys()
    assert inputdata['AcquisitionTime'] != outputdata['AcquisitionTime']

    # Create the output data for swapping between subjects, but not between runs
    for funcjson in funcjsons:
        (tmp_path/'output'/funcjson).unlink()
    scramble_swap(tmp_path/'input', tmp_path/'output', r'.*/sub-.*\.json', ['subject'], False)
    for funcjson in funcjsons:
        assert (tmp_path/'output'/funcjson).is_file()

    # Check that the json data is swapped
    for funcjson in funcjsons[0:3]:                                         # NB: make it extremely rare to fail due to random sampling (only when failing 3 times in a row)
        inputdata, outputdata = load_data(funcjson)
        if inputdata['AcquisitionTime'] != outputdata['AcquisitionTime']: break
    assert inputdata['AcquisitionTime'] != outputdata['AcquisitionTime']

    # Check that the run-05 json data is not swapped
    inputdata, outputdata = load_data(funcjsons[-1])
    assert inputdata['AcquisitionTime'] == outputdata['AcquisitionTime']


def test_scramble_pseudo(tmp_path):

    # Create the input data
    for sub in list(range(2,11)) + [12]:
        print('Downloading:', f"sub-{sub:02}/eeg/..")
        tsvpath  = f"sub-{sub:02}/eeg/sub-{sub:02}_task-MIvsRest_run-0_channels.tsv"
        edfpath  = f"sub-{sub:02}/eeg/sub-{sub:02}_task-MIvsRest_run-0_eeg.edf"
        jsonpath = f"sub-{sub:02}/eeg/sub-{sub:02}_task-MIvsRest_run-0_eeg.json"
        (tmp_path/'input'/f"sub-{sub:02}"/'eeg').mkdir(parents=True)
        urllib.request.urlretrieve(f"https://s3.amazonaws.com/openneuro.org/ds003810/{tsvpath}", tmp_path/'input'/tsvpath)
        urllib.request.urlretrieve(f"https://s3.amazonaws.com/openneuro.org/ds003810/{edfpath}", tmp_path/'input'/edfpath)
        urllib.request.urlretrieve(f"https://s3.amazonaws.com/openneuro.org/ds003810/{jsonpath}", tmp_path/'input'/jsonpath)
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds003810/participants.tsv', tmp_path/'input'/'participants.tsv')
    urllib.request.urlretrieve('https://s3.amazonaws.com/openneuro.org/ds003810/participants.tsv', tmp_path/'input'/'participants.json')
    (tmp_path/'input'/'.bidsignore').touch()
    (tmp_path/'input'/'.git').mkdir()

    # Pseudonymize the data using permuted subject identifiers
    scramble_pseudo(tmp_path/'input', tmp_path/'output', r'(?!\.).*', True, 'permute', '^sub-(.*?)(?:/|$).*', 'yes')
    assert (tmp_path/'output'/'participants.json').is_file()
    assert (tmp_path/'output'/edfpath).is_file()
    assert (tmp_path/'output'/'.bidsignore').is_file()
    assert not (tmp_path/'output'/'.git').exists()

    # Check the participants.tsv file
    inputdata  = pd.read_csv(tmp_path/'input'/'participants.tsv', sep='\t', index_col='participant_id')
    outputdata = pd.read_csv(tmp_path/'output'/'participants.tsv', sep='\t', index_col='participant_id')
    assert outputdata.shape == inputdata.shape
    for column, values in outputdata.items():
        assert column in inputdata.columns
    assert not inputdata.index.equals(outputdata.index)
    for index in inputdata.index:
        assert index in outputdata.index

    # Pseudonymize the n=1 data using random subject identifiers
    shutil.rmtree(tmp_path/'output')
    scramble_pseudo(tmp_path/'input', tmp_path/'output', r'sub-03(/|$).*', True, 'random', '^sub-(.*?)(?:/|$).*', 'yes')
    assert (tmp_path/'output'/'participants.json').is_file()
    assert not (tmp_path/'output'/edfpath).exists()

    # Check the participants.tsv file
    outputdata = pd.read_csv(tmp_path/'output'/'participants.tsv', sep='\t', index_col='participant_id')
    assert outputdata.shape == (1, inputdata.shape[1])
    for column, values in outputdata.items():
        assert column in inputdata.columns
    assert not inputdata.index.equals(outputdata.index)
    for index in inputdata.index:
        assert index not in outputdata.index

    # Pseudonymize the n-1 data using random subject identifiers
    shutil.rmtree(tmp_path/'output')
    scramble_pseudo(tmp_path/'input', tmp_path/'output', r'(?!sub-03(/|$)).*', True, 'random', '^sub-(.*?)(?:/|$).*', 'yes')
    assert (tmp_path/'output'/'participants.json').is_file()
    assert not (tmp_path/'output'/edfpath).exists()

    # Check the participants.tsv file
    outputdata = pd.read_csv(tmp_path/'output'/'participants.tsv', sep='\t', index_col='participant_id')
    assert outputdata.shape == (inputdata.shape[0] - 1, inputdata.shape[1])
    for column, values in outputdata.items():
        assert column in inputdata.columns
    assert not inputdata.index.equals(outputdata.index)
    for index in inputdata.index:
        assert index not in outputdata.index

    # Create inputdir + derivatives with 3 subjects
    table = pd.DataFrame().rename_axis('participant_id')
    input = tmp_path/'input'
    for label in range(3):
        subdir = input/f"sub-{label}"
        (subdir/'anat').mkdir(parents=True)
        (subdir/'anat'/f"sub-{label}_T1w.nii").touch()
        (subdir/'anat'/f"sub-{label}_T1w.json").touch()
        table.loc[f"sub-{label}", 'inputdir'] = label
    table.to_csv(input/'participants.tsv', sep='\t')
    (input/'README').touch()
    derivative = input/'derivatives'/'deriv-1'
    derivative.parent.mkdir()
    shutil.copytree(input, derivative, ignore=shutil.ignore_patterns('derivatives'))
    (input/'sub-0_T1w.html').touch()
    (input/'sub-1_T1w.html').touch()
    (derivative/'sub-0_T1w.html').touch()                   # This is what MRIQC does
    (derivative/'sub-1_T1w.html').touch()
    derivative = input/'derivatives'/'deriv-2'
    shutil.copytree(input, derivative, ignore=shutil.ignore_patterns('derivatives'))

    # Test leave-one-out
    exclude = r'(?!(.*/)*sub-1([\._-].+)*(/|$)).*'           # = NO: PID folder, files starting with PID_ or PID-
    scramble_pseudo(tmp_path/'input', tmp_path/'output', exclude, False, 'original','^sub-(.*?)(?:/|$).*', 'no')
    assert     (tmp_path/'output'/'sub-0').is_dir()
    assert     (tmp_path/'output'/'sub-0'/'anat'/'sub-0_T1w.nii').is_file()
    assert     (tmp_path/'output'/'sub-0_T1w.html').exists()
    assert not (tmp_path/'output'/'sub-1').exists()
    assert not (tmp_path/'output'/'sub-1'/'anat'/'sub-1_T1w.nii').exists()
    assert not (tmp_path/'output'/'sub-1_T1w.html').exists()
    assert     (tmp_path/'output'/'derivatives'/'deriv-1'/'sub-0').is_dir()
    assert     (tmp_path/'output'/'derivatives'/'deriv-1'/'sub-0'/'anat'/'sub-0_T1w.nii').is_file()
    assert not (tmp_path/'output'/'derivatives'/'deriv-1'/'sub-1').exists()
    assert not (tmp_path/'output'/'derivatives'/'deriv-1'/'sub-1'/'anat'/'sub-1_T1w.nii').exists()
    assert     (tmp_path/'output'/'derivatives'/'deriv-1'/'sub-0_T1w.html').exists()
    assert not (tmp_path/'output'/'derivatives'/'deriv-1'/'sub-1_T1w.html').exists()
    assert     (tmp_path/'output'/'derivatives'/'deriv-2'/'sub-2'/'anat'/'sub-2_T1w.nii').is_file()
