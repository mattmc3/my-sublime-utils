import unittest
from utils import SqlUtil


class TestSqlUtil(unittest.TestCase):
    def test_init_object(self):
        util = SqlUtil()
        self.assertTrue(util is not None)


if __name__ == '__main__':
    unittest.main()
