import unittest

from hpb.utils.kahn_algo import KahnAlgo


class TestKahnAlgo(unittest.TestCase):
    def test_without_cycle(self):
        edges = [
            [0, 2],
            [1, 2],
            [1, 3],
            [4, 3],
            [2, 4],
        ]
        kahn = KahnAlgo()
        result = kahn.sort(5, edges)

        self.assertIsNotNone(result)
        if result is None:
            # for get rid of editor warning
            return

        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], 2)
        self.assertEqual(result[3], 4)
        self.assertEqual(result[4], 3)

    def test_with_cycle(self):
        edges = [
            [0, 1],
            [1, 2],
            [2, 1],
        ]
        kahn = KahnAlgo()
        result = kahn.sort(3, edges)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
