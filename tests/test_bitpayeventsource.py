#!/usr/bin/env python

import unittest

from bitpayeventsource import BitPayEventSource

class Test(unittest.TestCase):
    def test_one(self):
        event_source = BitPayEventSource('7ij57s6enEmja36x2G3efJ8k5zVxEBPjgRWsAa8jbg8B1stptUzvBYvQAfoa6q2eYq')
        event_source.start()

if __name__ == '__main__':
    unittest.main()
