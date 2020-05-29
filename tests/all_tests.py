#!/usr/bin/env python3
import unittest
import sys

suite = unittest.TestLoader().loadTestsFromNames(
    [
        'test_testinfo',
        'test_pathmatchinfo',
        'test_listinfo',
        'test_multiclassinfo',
        'test_parsers'
    ]
)

testresult = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if testresult.wasSuccessful() else 1)
