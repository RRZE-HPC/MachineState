#!/usr/bin/env python3
"""
High-level tests for get_html()
"""

import machinestate
import requests
import unittest
import json

class TestGetHtml(unittest.TestCase):
    def setUp(self):
        self.ms = machinestate.MachineState()
        self.ms.generate()
        self.ms.update()
    def test_getHTML(self):
        html = machinestate.get_html(self.ms)
        self.assertIsNotNone(html)
        self.assertNotEqual(html, "")
    def test_validateHTML(self):
        html = machinestate.get_html(self.ms)
        r = requests.post('https://validator.w3.org/nu/', 
                            data=html, 
                            params={'out': 'json'}, 
                            headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36', 
                            'Content-Type': 'text/html; charset=UTF-8'})
        if r and r.status_code == requests.codes.ok:
            res = r.json()
            self.assertIsNotNone(res)
            self.assertNotEqual(res, {})
            messages = res.get("messages", None)
            self.assertIsNotNone(messages)
            elist = []
            for msg in messages:
                if msg['type'] == "error":
                    elist.append("{}: L{}-{} - {}".format(msg['type'].title(),
                                                          msg['firstLine'],
                                                          msg['lastLine'],
                                                          msg['message']))
            self.assertEqual(len(elist), 0, msg="\n"+"\n".join(elist))
        else:
            self.skipTest("Cannot validate using validator.w3.org")
