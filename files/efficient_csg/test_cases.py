import unittest
import numpy as np
import csg

class TestArrayCSGOperation(unittest.TestCase):
    def setUp(self) -> None:
        self.array1 = np.array((1, 4, 5, 10))
        self.array2 = np.array((0, 2, 3, 5, 6, 7, 8, 9, 11, 12))
        self.expected = np.full(self.array1.shape[0] + self.array2.shape[0], np.inf)

    def test_add_operation(self):
        unioned = csg.array_csg(self.array1, self.array2, csg.Operation.UNION)
        self.expected[:4] = (0, 10, 11, 12)
        self.assertTrue(np.allclose(unioned, self.expected), f"expected {self.expected} but got {unioned}")

    def test_intersection_operation(self):
        intersected = csg.array_csg(self.array1, self.array2, csg.Operation.INTERSECT)
        self.expected[:10] = (1, 2, 3, 4, 5, 5, 6, 7, 8, 9)
        self.assertTrue(np.allclose(intersected, self.expected), f"expected {self.expected} but got {intersected}")

    def test_diff_operation(self):
        diffed = csg.array_csg(self.array1, self.array2, csg.Operation.DIFFERENCE)
        self.expected[:8] = (2, 3, 5, 6, 7, 8, 9, 10)
        self.assertTrue(np.allclose(diffed, self.expected), f"expected {self.expected} but got {diffed}")


if __name__ == '__main__':
    unittest.main()