import numpy as np

def find_closest_point(_target, _arr):
    if _target <= _arr[0]:
        return _arr[0]

    if _target >= _arr[-1]:
        return _arr[-1]

    closest = _arr[0]
    for e in _arr:
        if abs(_target-e) < abs(_target-closest):
            closest = e

        if e > _target:
            return closest

    return closest


if __name__ == '__main__':
    target = 3.3
    arr = np.arange(0, 10, 0.5)

    print('target: {}'.format(target))
    print('arr: {}'.format(arr))
    print(find_closest_point(target, arr))
