from math_helper import compute_average
def test_avg():
    assert compute_average([10, 20]) == 15.0
    assert compute_average([]) == 0.0
