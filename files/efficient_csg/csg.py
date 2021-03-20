import numpy as np
from enum import Enum

class Operation(Enum):
    UNION = 1
    INTERSECT = 2
    DIFFERENCE = 3


def array_csg(array1: np.ndarray, array2: np.ndarray, operation: Operation, sort_output=True):
    """
    Given two arrays and an operation, returns a new array which is the CSG operation acting on the array.
    If the array is thought of as intersection points between a ray and a two objects being combined with a CSG
    operation, the returned is the valid hits for the resulting object. Function assumes both arrays are sorted and have
    an even number of axis=0 elements

    :param array1:
    :param array2:
    :param operation:
    :return:
    """

    if array1.ndim == 1:
        # if 1D arrays were passed, concatenate
        merged_array = np.concatenate((array1, array2))
        merged_argsort = np.argsort(merged_array, axis=0)
        merged_array = merged_array[merged_argsort]

    else:
        # otherwise stack them where each column represents a unique ray's hits
        merged_array = np.vstack((array1, array2))
        merged_argsort = np.argsort(merged_array, axis=0)
        merged_array = merged_array[merged_argsort, np.arange(merged_array.shape[-1])]


    if operation == Operation.UNION or operation == Operation.INTERSECT:
        merged_mask = np.where(merged_argsort & 1, -1, 1)
        surface_count = np.cumsum(merged_mask, axis=0)

    elif operation == Operation.DIFFERENCE:
        merged_mask = np.where(np.logical_xor(merged_argsort & 1, merged_argsort >= array1.shape[0]), -1, 1)
        surface_count = np.cumsum(merged_mask, axis=0) + 1
    else:
        raise ValueError(f"operation {operation} is invalid")

    if operation == Operation.UNION:
        surface_count = np.logical_xor(surface_count, np.roll(surface_count,1,axis=0))
        csg_hits = np.where(surface_count != 0, merged_array, np.inf)

    elif operation == Operation.INTERSECT or operation == Operation.DIFFERENCE:
        is_two = (surface_count == 2)
        mask = np.logical_or(is_two, np.roll(is_two, 1, axis=0))
        csg_hits = np.where(mask, merged_array, np.inf)

    return np.sort(csg_hits, axis=0) if sort_output else csg_hits


