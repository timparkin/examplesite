"""
Simple enumeration type.
"""


class Enum(object):

    def __init__(self, *items):
        self._items = list(_normalize_items(items))

    def items(self):
        return iter(self._items)

    def names(self):
        return (i[0] for i in self._items)

    def values(self):
        return (i[1] for i in self._items)

    def value_of(self, name):
        for item in self._items:
            if item[0] == name:
                return item[1]
        raise KeyError(name)

    def name_of(self, value):
        for item in self._items:
            if item[1] == value:
                return item[0]
        raise ValueError(value)

    def __contains__(self, value):
        return value in [i[1] for i in self._items]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self.items())

    __getattr__ = value_of
    __getitem__ = name_of


def _normalize_items(items):
    for item in items:
        if isinstance(item, tuple):
            yield item
        else:
            yield (item, item)


if __name__ == '__main__':

    import unittest

    class TestEnum(unittest.TestCase):

        def setUp(self):
            self.colours = Enum('RED', 'GREEN', 'BLUE')
            self.numbers = Enum(("One", 1), ("Two", 2), ("Three", 3), ("Four", 4))

        def test_len(self):
            self.assertEquals(len(self.colours), 3)
            self.assertEquals(len(self.numbers), 4)

        def test_contains(self):
            self.assertTrue('RED' in self.colours)
            self.assertTrue(1 in self.numbers)
            self.assertFalse('PINK' in self.colours)
            self.assertFalse(82 in self.colours)

        def test_items(self):
            self.assertEquals(list(self.colours.items()), [("RED", "RED"),
                ("GREEN", "GREEN"), ("BLUE", "BLUE")])
            self.assertEquals(list(self.numbers.items()), [("One", 1),
                ("Two", 2), ("Three", 3), ("Four", 4)])

        def test_names(self):
            self.assertEquals(list(self.colours.names()), ["RED", "GREEN", "BLUE"])
            self.assertEquals(list(self.numbers.names()), ["One", "Two", "Three", "Four"])

        def test_values(self):
            self.assertEquals(list(self.colours.values()), ["RED", "GREEN", "BLUE"])
            self.assertEquals(list(self.numbers.values()), [1, 2, 3, 4])

        def test_value_of(self):
            self.assertEquals(self.colours.value_of('RED'), 'RED')
            self.assertEquals(self.colours.value_of('GREEN'), 'GREEN')
            self.assertEquals(self.colours.value_of('BLUE'), 'BLUE')
            self.assertEquals(self.numbers.value_of('One'), 1)
            self.assertEquals(self.numbers.value_of('Two'), 2)
            self.assertEquals(self.numbers.value_of('Three'), 3)
            self.assertEquals(self.numbers.value_of('Four'), 4)
            self.assertRaises(KeyError, self.numbers.value_of, 'Ten')

        def test_name_of(self):
            self.assertEquals(self.colours.name_of('RED'), 'RED')
            self.assertEquals(self.numbers.name_of(1), 'One')
            self.assertRaises(ValueError, self.numbers.name_of, 10)

        def test_getattr(self):
            self.assertEquals(self.colours.RED, 'RED')
            self.assertEquals(self.numbers.One, 1)

        def test_getitem(self):
            self.assertEquals(self.colours['RED'], 'RED')
            self.assertEquals(self.numbers[1], 'One')

    unittest.main()

