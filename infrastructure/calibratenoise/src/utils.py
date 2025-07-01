import numpy as np

class TSVHandler:
    
    def save(self, filepath,array: np.ndarray):

        np.savetxt(filepath, array, delimiter='\t', fmt='%.6f')

    def load(self, filepath) -> np.ndarray:

        return np.loadtxt(filepath, delimiter='\t')
