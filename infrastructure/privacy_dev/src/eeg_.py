import os, mne
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")
mne.set_log_level("ERROR")

BIDS_ROOT = "/staff/vincentajoubi/Trash/wp15-chrono-T/usecase-2.4/input"
def eeg_(BIDS_ROOT):
    vhdr_path, channels_tsv = None, None
    for root, dirs, files in os.walk(BIDS_ROOT):
        for f in files:
            if f.endswith("_eeg.vhdr"):
                vhdr_path = os.path.join(root, f)
            if f.endswith("_channels.tsv"):
                channels_tsv = os.path.join(root, f)
        if vhdr_path and channels_tsv:
            break
    
    
    raw = mne.io.read_raw_brainvision(vhdr_path, preload=True)
    
    channels_df = pd.read_csv(channels_tsv, sep="\t")
    chan_types = {row["name"]: row["type"].lower() for _, row in channels_df.iterrows()}
    raw.pick_channels(channels_df["name"].tolist())
    raw.set_channel_types(chan_types)
    
    montage = mne.channels.make_standard_montage("standard_1020")
    raw.set_montage(montage, match_case=False)
    adjacency, ch_names = mne.channels.find_ch_adjacency(raw.info, ch_type="eeg")
    dense = adjacency.toarray()
    
    all_neigh = [
        np.stack([raw.get_data(picks=n) for n, flag in zip(ch_names, dense[idx]) if flag]).reshape(-1, 1)
        for idx in range(len(ch_names))]
    
    return all_neigh
