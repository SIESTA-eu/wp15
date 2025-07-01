import numpy as np

def sensitivity(data):

    return np.abs(np.max(data) - np.min(data))
    
def laplace_mechanism(data, epsilon, sensitivity_):

    scale = sensitivity_ / epsilon
    noise = np.random.laplace(loc=0.0, scale=scale, size=data.shape)
    
    return data + noise
    

