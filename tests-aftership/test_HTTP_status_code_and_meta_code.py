# -*- coding: utf-8 -*-
# jsonschema2.6.0 Full support for Draft 3 and Draft 4 of the schema.
# Created by Jiapei Chen on 2018-05-11

import unittest
import requests


'''Test on all implemented HTTP status code

Including meta code 200, 400, 4001, 4002, 403, 404, 413, 415, 500
Meta code 429 is not tested.
'''
class TestYunexpress(unittest.TestCase):

    def setUp(self):
        self.url = "http://127.0.0.1:9080/trackings"
        self.headers = {
            "Content-Type": "application/json",
            "aftership-courier-api-key": "aftership-spider-team"
        }
        self.data = '''
        {
            "slug": "aftership",
            "tracking_queries": [
                {
                    "tracking_number": "YT1802927571800445"
                }
            ]
        }
        '''

    def test_health_check(self):
        resp = requests.get(self.url)
        self.assertEqual(resp.status_code, 200)

    # invalid request JSON
    def test_meta_code_400(self):
        # missing the last right bracket
        self.data = '''
        {
            "slug": "aftership",
            "tracking_queries": [
                {
                    "tracking_number": "YT1802927571800445"
                }
            ]
        '''
        resp = requests.post(url=self.url,
                             data=self.data,
                             headers=self.headers)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp_json['meta']['code'], 400)
        self.assertEqual(resp_json['meta']['message'], "Invalid JSON")

    # invalid request payload
    def test_meta_code_4001(self):
        # 'tracking_queries' with missing 's'
        self.data = '''
        {
            "slug": "aftership",
            "tracking_querie": [
                {
                    "tracking_number": "YT1802927571800445"
                }
            ]
        }
        '''
        resp = requests.post(url=self.url,
                             data=self.data,
                             headers=self.headers)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp_json['meta']['code'], 4001)
        self.assertEqual(resp_json['meta']['message'], "Invalid payload")

    # invalid request slug
    def test_meta_code_4002(self):
        # 'yunexpress' with missing 'ss'
        self.data = '''
        {
            "slug": "aftership",
            "tracking_queries": [
                {
                    "tracking_number": "YT1802927571800445"
                }
            ]
        }
        '''
        resp = requests.post(url=self.url,
                             data=self.data,
                             headers=self.headers)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp_json['meta']['code'], 4002)
        self.assertEqual(resp_json['meta']['message'], "Invalid slug")

    # invalid API key
    def test_meta_code_403_wrong_api_key(self):
        # change 'api_key' from 'team' to 'xxxx'
        self.headers = {
            "Content-Type": "application/json",
            "aftership-courier-api-key": "aftership-spider-xxxx"
        }
        resp = requests.post(url=self.url,
                             data=self.data,
                             headers=self.headers)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp_json['meta']['code'], 403)
        self.assertEqual(resp_json['meta']['message'], "Invalid API key")

    # invalid API key
    def test_meta_code_403_no_api_key(self):
        # missing 'api_key'
        self.headers = {
            "Content-Type": "application/json"
        }
        resp = requests.post(url=self.url,
                             data=self.data,
                             headers=self.headers)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp_json['meta']['code'], 403)
        self.assertEqual(resp_json['meta']['message'], "Invalid API key")

    # end point not found
    def test_meta_code_404(self):
        # end point '/trackings' missing 's'
        self.url = "http://127.0.0.1:9080/tracking"
        resp = requests.post(url=self.url,
                             data=self.data,
                             headers=self.headers)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp_json['meta']['code'], 404)
        self.assertEqual(resp_json['meta']['message'], "Not found")

    # payload too large
    def test_meta_code_413(self):
        resp = requests.post(url=self.url,
                             data=self.data,
                             headers=self.headers)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, 413)
        self.assertEqual(resp_json['meta']['code'], 413)
        self.assertEqual(resp_json['meta']['message'], "Payload too large")

    # unsupported 'Content-Type'
    def test_meta_code_415(self):
        # change 'Content-Type' from 'application/json' to 'text/html'
        self.headers = {
            "Content-Type": "text/html",
            "aftership-courier-api-key": "aftership-spider-team"
        }
        resp = requests.post(url=self.url,
                             data=self.data,
                             headers=self.headers)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, 415)
        self.assertEqual(resp_json['meta']['code'], 415)
        self.assertEqual(resp_json['meta']['message'], "Unsupported media type")

    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
