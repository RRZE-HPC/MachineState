#!/usr/bin/env python3
"""
High-level tests for get_html()
"""

from machinestate import MachineState
import requests
import unittest

class TestGetHtml(unittest.TestCase):
    def test_getHTML(self):
        ms = MachineState()
        ms.generate()
        ms.update()
        html = get_html(ms)
        r = requests.post('https://validator.w3.org/nu/', 
                            data=html, 
                            params={'out': 'json'}, 
                            headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36', 
                            'Content-Type': 'text/html; charset=UTF-8'})
        res = r.json()
        self.assertIsNotNone(res)
        self.assertIsNotNone(res.get("message", None))
        self.assertEqual(res["message"], [])
