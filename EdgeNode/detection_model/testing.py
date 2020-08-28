import numpy as np
from sklearn.preprocessing import normalize, StandardScaler


def a():
    temp = np.array([[1, 2, 3],
                     [2, 4, 6],
                     [3, 6, 9]])
    norm1 = normalize(temp, axis=0)
    norm2 = normalize(temp, axis=1)
    scaler = StandardScaler()
    scaler.fit(temp)
    norm3 = scaler.transform(temp)
    return norm1, norm2, norm3



