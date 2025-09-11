from joblib import Parallel, delayed
import numpy as np
import warnings, sys, os, time, copy, traceback, random
warnings.filterwarnings("ignore")
from numba import njit, prange
import matplotlib.pyplot as plt
import seaborn as sns
from src.loader import *
from src.utils import *
from src.src import *
from rich import print
from src.eeg_ import eeg_

def main(path_list, Dim4=False):


    tasks = ["ERN","LRP","MMN","N2pc","N170","N400","P3"]
    task_order = {task: idx for idx, task in enumerate(tasks)}

    def task_(path):
        for task in tasks:
            if f"_task-{task}_" in path or f"/ses-{task}/" in path:
                return task
        return None 

    values_sorted = sorted(path_list, key=lambda x: task_order.get(task_(x), float('inf')))

    def process_channel(channel_idx, p_):
        try:
            data = np.stack([np.array(eeg_("/".join(p.split('/')[:-4]))[channel_idx].flatten()) for p in p_])
            original_output = user_pipeline(data)
            noisy_outputs, sensitivities = dp(data, original_output)
            return noisy_outputs, sensitivities
        except IndexError:
            return None

    for task in tasks:
        print("="*10, task, "="*10)
        p_ = [path for path in values_sorted if task in path]
        all_noisy_outputs, all_sensitivities = list(), list()
        results = Parallel(n_jobs=-1)(delayed(process_channel)(ch, p_) for ch in range(len(p_)))
        results = [r for r in results if r is not None]
            
        all_noisy_outputs, all_sensitivities = zip(*results)
        
        print(np.stack(all_noisy_outputs).shape)
        print("="*25)
        
        break
    #return #noisy_outputs, sensitivities, int(failed)

    
    
  
def process_(original_list, data_type):

    try:
        args = {"path_list": original_list}
        _ = main(**args)
    except Exception as e:
        traceback.print_exc()
    #########################################
    #             MAIN CALL                 #
    #########################################  

if __name__ == "__main__":
    
    start_time = time.time()
    try:
        if len(sys.argv) < 2:
            raise ValueError("Insufficient arguments")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

 
    usecase = 2.4
    if usecase == None:
        orig = sys.argv[1]
    elif usecase == 2.2:
        orig = "/staff/vincentajoubi/Trash/wp15-usecase-2.1_aux/usecase-2.2/input/"
    elif usecase == 2.3:
        orig = "/staff/vincentajoubi/wp15-chrono-T/usecase-2.3/input/"
    elif usecase == 2.4:
        orig = "/staff/vincentajoubi/Trash/wp15-chrono-T/usecase-2.4/input/"# sub-001/
    elif usecase == 2.5:
        orig = "/staff/vincentajoubi/wp15-chrono-T/usecase-2.5/input/"

    if detect_file(orig) == "nii":
        process_(fetch_files(orig).nii_(), data_type="func")
    if detect_file(orig) == "fif":
        process_(fetch_files(orig).fif_(), data_type="fif")
    if detect_file(orig) == "vhdr":
        process_(fetch_files(orig).vhdr_(), data_type="vhdr")

        
    total_time = time.time() - start_time
    print(f"\nTotal time taken: {time.strftime('%H:%M:%S', time.gmtime(total_time))}")

