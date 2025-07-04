import sys
import numpy as np

from src.utils import * 

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python calibratenoise.py <input.tsv> <output.tsv>")
        sys.exit(1)
    

    data_in  = sys.argv[1]
    data_out = sys.argv[2] 
    
    tsv = TSVHandler()
    participants = tsv.load(data_in)
    all_noise = np.full(participants.shape[1], np.nan)

    for participant in range(participants.shape[1]):
        loo_estimate = participants[:, participant]
        
        true_mean = np.mean(loo_estimate)
        aprx_mean = loo_estimate

        sensitivity = np.max(np.abs(true_mean - aprx_mean)) 
        noise = np.random.laplace(loc=0.0, scale=sensitivity)
        all_noise[participant] = noise
        
    tsv.save(data_out, all_noise, transpose=True) # if transpose = False, then each value in a new line
    
    #sensitivity = l1_sens(data)
    #epsilon = 0.5
    #private_data = laplace_mechanism(data, epsilon, sensitivity)
    
