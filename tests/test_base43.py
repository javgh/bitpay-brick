#!/usr/bin/env python

import unittest

import base43

class Test(unittest.TestCase):
    def test_matches_schildbach_wallet_behavior(self):
        self.assertEqual(base43.encode("http"), "B-PQDS")
        self.assertEqual(base43.encode("\x00\x00\x2A"), "00:")

if __name__ == '__main__':
    unittest.main()
