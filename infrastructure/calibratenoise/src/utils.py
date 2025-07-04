import numpy as np

class TSVHandler:
    
    def save(self, filepath, array: np.ndarray, transpose = False):
        if transpose:
            np.savetxt(filepath, array.reshape(1,-1), delimiter='\t', fmt='%.6f')
            
        else: np.savetxt(filepath, array, delimiter='\t', fmt='%.6f')

    def load(self, filepath) -> np.ndarray:
        
        return np.loadtxt(filepath, delimiter='\t')
