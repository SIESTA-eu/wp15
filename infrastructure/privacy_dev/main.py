import numpy as np
import warnings, sys, os, tqdm, time, copy, traceback, random
warnings.filterwarnings("ignore")
from numba import njit, prange
import matplotlib.pyplot as plt
import seaborn as sns
from src.loader import *
from src.viz import *
from src.utils import *
from src.src import *
from rich import print
from src.eeg_ import eeg_

def main(path, path_list, Dim4=False):

    ext = path.split("/")[-1]
    if ext.endswith(".nii") or ext.endswith(".nii.gz"):
        data = nii_reader(path).get_data()
        if len(list(original.shape)) == 4:
            Dim4 = True
    elif ext.endswith(".fif") \
        or ext.endswith(".fif.gz") \
        or ext.endswith(".vhdr") \
        or ext.endswith(".vhdr.gz"):
        data = neuro_reader(path).get_data()
        
    else: 
        print(f" - Unsupported file type.")
    print("=" * 30)

    tasks = ["ERN","LRP","MMN","N2pc","N170","N400","P3"]
    task_order = {task: idx for idx, task in enumerate(tasks)}
    def task_(path):
        for task in tasks:
            if f"_task-{task}_" in path or f"/ses-{task}/" in path:
                return task
        return None 
    values_sorted = sorted(path_list, key=lambda x: task_order.get(task_(x), float('inf')))
    
    for t in tasks:
        p_ = [v for v in values_sorted if t in v]
        for c in range(30):
            data = np.stack([np.array(eeg_("/".join(p.split('/')[:-4]))[c].flatten(), dtype=object) for p in p_])
            original_output = user_pipeline(data)
            noisy_outputs, sensitivities = dp(data, original_output)  
            break
            print(original_output.shape)
        break
    print("=" * 30)
    

    #with warnings.catch_warnings(record=True) as w:
    #    warnings.simplefilter("always")
    #    noisy_outputs, sensitivities = dp(data, original_output)    
    #    failed = any("Failed to generate correlated noise" in str(msg.message) for msg in w)

    #return #noisy_outputs, sensitivities, int(failed)

    
    
  
def process_(original_list, data_type):
    for o in original_list: # 
        try:
            #file_ = neuro_reader(o).get_data() if "fif" in o or "vhdr" in o else nii_reader(o).get_data()
            args = {"path": o,
                    "path_list": original_list}
            _ = main(**args)
        except Exception as e:
            traceback.print_exc()
        break
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

