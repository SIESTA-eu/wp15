import pandas as pd
import shutil
from bidscramble.merge import merge

def test_merge(tmp_path):

    # Create 3 inputdirs + derivatives with 1, 2 and 3 subjects, respectively
    for idx in range(1, 4):
        table = pd.DataFrame().rename_axis('participant_id')
        inputdir = tmp_path/f"input-{idx}"
        for label in range(2*idx, 3*idx):
            subdir = inputdir/f"sub-{label}"
            (subdir/'anat').mkdir(parents=True)
            (subdir/'anat'/f"sub-{label}_T1w.nii").touch()
            (subdir/'anat'/f"sub-{label}_T1w.json").touch()
            table.loc[f"sub-{label}", 'inputdir'] = idx
        table.to_csv(inputdir/'participants.tsv', sep='\t')
        (inputdir/'README').touch()
        derivative = inputdir/'derivatives'/'deriv-1'
        derivative.parent.mkdir()
        shutil.copytree(inputdir, derivative, ignore=shutil.ignore_patterns('derivatives'))
        derivative = inputdir/'derivatives'/'deriv-2'
        shutil.copytree(inputdir, derivative, ignore=shutil.ignore_patterns('derivatives'))

    # Merge the inputdirs
    merge([tmp_path/f"input-{idx}" for idx in range(1, 4)], merged := tmp_path/'merged')

    assert len(list(merged.iterdir()))                               == 9       # 6 subjects + derivatives + README + participants.tsv
    assert len(list(merged.glob('sub-*')))                           == 6       # 6 subjects
    assert len(list(merged.rglob('*.nii')))                          == 3 * 6   # 6 subjects in root + 6 subjects in each of the 2 derivatives
    assert len(list((merged/'derivatives').iterdir()))               == 2       # 2 derivatives
    assert len(list((merged/'derivatives'/'deriv-1').iterdir()))     == 8       # 6 subjects + README + participants.tsv
    assert len(list((merged/'derivatives'/'deriv-1').glob('sub-*'))) == 6       # 6 subjects

    table = pd.read_csv(merged/'participants.tsv', sep='\t', dtype=str, index_col='participant_id')
    assert table.shape == (6, 1)
    assert table.loc['sub-2', 'inputdir'] == '1.0'
    assert table.loc['sub-4', 'inputdir'] == '2.0'
    assert table.loc['sub-6', 'inputdir'] == '3.0'
    assert table.equals(pd.read_csv(merged/'derivatives'/'deriv-1'/'participants.tsv', sep='\t', dtype=str, index_col='participant_id'))
