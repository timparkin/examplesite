from examplesite.tests import base


class TestRoot(base.TestCase):

    def test_get(self):
        self.app.get('/')


if __name__ == '__main__':
    import unittest
    unittest.main()

