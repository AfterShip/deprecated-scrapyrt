# -*- coding: utf-8 -*-

import json
import copy
import pytest
import re
from mock import MagicMock, patch, Mock
from twisted.web.error import Error
from twisted.web.server import Request
from scrapyrt.resources import CrawlResource




@pytest.fixture()
def t_req():
    return MagicMock(spec=Request)


@pytest.fixture()
def resource():
    return CrawlResource()


class TestCrawlResource(object):

    def test_render_GET(self,t_req,resource):
        expected_response = {
            "meta": {
                "message": "OK",
                "code": 200
            }
        }
        response = resource.render_GET(t_req)
        for key, value in expected_response.items() :
            assert response[key] == value

    @pytest.mark.parametrize('scrapy_args,api_args,has_error', [
        ({'url': 'aa'}, {}, False),
        ({}, {}, True)
    ])

    def test_validate_options(self, resource,scrapy_args, api_args, has_error):
        if has_error:
            with pytest.raises(Error) as e:
                resource.validate_options(scrapy_args, api_args)
            assert e.value.status == '400'
            assert re.search("\'url\' is required", e.value.message)
        else:
            result = resource.validate_options(scrapy_args, api_args)
            assert result is None

    def test_prepare_response(self, resource):
        items_json = '''[
      {
        "slug": "yunexpress",
        "tracking_number": "YT1802927571800445",
        "additional_fields": null,
        "checkpoints": [
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "NORTH STREET, MI"
            },
            "date_time": {
              "date": "2018-04-05",
              "time": "11:51:00",
              "utf": null
            },
            "message": "Delivered",
            "raw_tag": 50,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "NORTH STREET, MI"
            },
            "date_time": {
              "date": "2018-04-05",
              "time": "09:43:00",
              "utf": null
            },
            "message": "Out for delivery",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "PORT HURON, MI"
            },
            "date_time": {
              "date": "2018-04-05",
              "time": "05:25:00",
              "utf": null
            },
            "message": "At U.S. Postal Service facility",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "PORT HURON, MI"
            },
            "date_time": {
              "date": "2018-04-04",
              "time": "03:03:00",
              "utf": null
            },
            "message": "In transit",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "FEDEX SMARTPOST BELLEVILLE, MI"
            },
            "date_time": {
              "date": "2018-04-04",
              "time": "02:23:44",
              "utf": null
            },
            "message": "Departed FedEx location",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "FEDEX SMARTPOST BELLEVILLE, MI"
            },
            "date_time": {
              "date": "2018-04-03",
              "time": "12:41:06",
              "utf": null
            },
            "message": "Arrived at FedEx location",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "PERRYSBURG, OH"
            },
            "date_time": {
              "date": "2018-04-02",
              "time": "23:14:12",
              "utf": null
            },
            "message": "Departed FedEx location",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "PERRYSBURG, OH"
            },
            "date_time": {
              "date": "2018-04-02",
              "time": "16:56:00",
              "utf": null
            },
            "message": "Arrived at FedEx location",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "PERRYSBURG, OH"
            },
            "date_time": {
              "date": "2018-04-02",
              "time": "10:32:26",
              "utf": null
            },
            "message": "In transit",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "PERRYSBURG, OH"
            },
            "date_time": {
              "date": "2018-04-01",
              "time": "22:29:56",
              "utf": null
            },
            "message": "In transit",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "PERRYSBURG, OH"
            },
            "date_time": {
              "date": "2018-04-01",
              "time": "10:27:27",
              "utf": null
            },
            "message": "In transit",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "PERRYSBURG, OH"
            },
            "date_time": {
              "date": "2018-03-31",
              "time": "22:21:26",
              "utf": null
            },
            "message": "In transit",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "KEASBEY, NJ"
            },
            "date_time": {
              "date": "2018-03-31",
              "time": "06:16:44",
              "utf": null
            },
            "message": "Departed FedEx location",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "KEASBEY, NJ"
            },
            "date_time": {
              "date": "2018-03-30",
              "time": "18:39:00",
              "utf": null
            },
            "message": "Arrived at FedEx location",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "NEW YORK - UNITED STATES OF AMERICA"
            },
            "date_time": {
              "date": "2018-03-29",
              "time": "08:00:21",
              "utf": null
            },
            "message": "Clearance processing complete at  GATEWAY",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "NEW YORK - UNITED STATES OF AMERICA"
            },
            "date_time": {
              "date": "2018-03-29",
              "time": "01:13:49",
              "utf": null
            },
            "message": "Arrived at JOHN F. KENNEDY INTERNATIONAL AIRPORT , Custom clearance processing.",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "HONGKONG - HONG KONG"
            },
            "date_time": {
              "date": "2018-03-28",
              "time": "15:37:39",
              "utf": null
            },
            "message": "Departed Facility in HONG KONG INTERNATIONAL AIRPORT",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "HONGKONG - HONG KONG"
            },
            "date_time": {
              "date": "2018-03-27",
              "time": "15:00:20",
              "utf": null
            },
            "message": "Arrived at Sort Facility HONG KONG INTERNATIONAL AIRPORT",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "SHENZHEN"
            },
            "date_time": {
              "date": "2018-03-26",
              "time": "22:11:35",
              "utf": null
            },
            "message": "Departed Facility in SHENZHEN",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": "SHENZHEN"
            },
            "date_time": {
              "date": "2018-03-26",
              "time": "20:15:51",
              "utf": null
            },
            "message": "Arrived at Sort Facility SHENZHEN",
            "raw_tag": 20,
            "raw_tag_description": null
          },
          {
            "address": {
              "contact_name": null,
              "company_name": null,
              "street_1": null,
              "street_2": null,
              "street_3": null,
              "city": null,
              "state": null,
              "postal_code": null,
              "country_iso3": null,
              "type": null,
              "raw_location": ""
            },
            "date_time": {
              "date": "2018-03-24",
              "time": "15:02:12",
              "utf": null
            },
            "message": "Shipment information received",
            "raw_tag": 10,
            "raw_tag_description": null
          }
        ],
        "origin_address": {
          "contact_name": null,
          "company_name": null,
          "street_1": null,
          "street_2": null,
          "street_3": null,
          "city": null,
          "state": null,
          "postal_code": null,
          "country_iso3": "CHN",
          "type": null,
          "raw_location": "China"
        },
        "destination_address": {
          "contact_name": null,
          "company_name": null,
          "street_1": null,
          "street_2": null,
          "street_3": null,
          "city": null,
          "state": null,
          "postal_code": null,
          "country_iso3": "CHN",
          "type": null,
          "raw_location": "China"
        },
        "weight": {
          "value": 1.386,
          "unit": "kg"
        },
        "insurance": null,
        "pickup_date_time": null,
        "delivered_date_time": null,
        "scheduled_delivery_date_time": null,
        "rescheduled_delivery_date_time": null,
        "customer_tracking_reference": null,
        "signed_by": null,
        "service_type": "USZXR",
        "service_type_name": "中美专线(特惠)",
        "package_count": 1,
        "supports_last_mile_tracking": true,
        "next_courier": null,
        "status": {
          "message": "OK",
          "code": 200
        }
      }
    ]'''
        items = json.loads(items_json)

        result = {
            'items': items,
            'stats': [99],
            'spider_name': 'yunexpressspider'
        }
        prepared_res = resource.prepare_response(result)
        expected = {
            "meta": {
                "message": "OK",
                "code": 200
            },
            "data": {
                "trackings": items
            }
        }
        for key, value in expected.items():
            assert prepared_res[key] == value


    def test_wrap_aftership_courier_api(self,resource):

        api_params = {
            "slug": "yunexpress",
            "tracking_queries": [
                {
                    "tracking_number": "YT1802927571800445"
                }
            ]
        }

        aftership_api_params = resource.wrap_aftership_courier_api(api_params)
        start_requests = True

        request = {
            'meta': copy.deepcopy(api_params),
            'dont_filter': True
        }

        expect_aftership_api_params = {
            'request': request,
            'start_requests': start_requests,
            'spider_name': 'yunexpressspider'
        }

        for key, value in expect_aftership_api_params.items():
            assert aftership_api_params[key] == value