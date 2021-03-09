#!/usr/bin/env python3
import unittest
import sys

suite = unittest.TestLoader().loadTestsFromNames(
    [
        'test_infogroup',
        'test_pathmatchinfo',
        'test_listinfo',
        'test_multiclassinfo',
        'test_parsers',
        'test_helpers',
        'test_dmidecode_file',
        'test_machinestate',
        'test_repr',
        'test_config',
        'test_fromdict',
    ]
)

testresult = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if testresult.wasSuccessful() else 1)
