# -*- coding: utf-8 -*-
from six.moves.configparser import (
    SafeConfigParser, NoOptionError, NoSectionError
)
import argparse
import os
import sys
import json
import demjson

from scrapy.utils.conf import closest_scrapy_cfg
from scrapy.utils.misc import load_object
from twisted.application import app
from twisted.application.internet import TCPServer
from twisted.application.service import Application
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web import resource

from .log import setup_logging, logger
from .conf import settings
from .utils import to_bytes, extract_api_params_from_request

from twisted.python.compat import intToBytes
from twisted.web.server import Request


class AfterShipErrorPage(resource.Resource):
    def __init__(self, status, brief, detail):
        resource.Resource.__init__(self)
        self.code = status
        self.brief = brief
        self.detail = detail

    def render(self, request):
        request.setResponseCode(self.code)

        api_params = extract_api_params_from_request(request)

        logger.info(api_params)

        if self.code == 404:
            message = "Not found"

        result = {
            "meta": {
                "message": message,
                "code": self.code
            },
            "data": api_params
        }
        logger.info(result)
        return to_bytes(json.dumps(result))

    def getChild(self, chnam, request):
        return self


class AfterShipNoResource(AfterShipErrorPage):
    def __init__(self, message):
        AfterShipErrorPage.__init__(self, 404, message, message)


def processingFailed(self, reason):
        """
        Finish this request with an indication that processing failed and
        possibly display a traceback.
        @param reason: Reason this request has failed.
        @type reason: L{twisted.python.failure.Failure}
        @return: The reason passed to this method.
        @rtype: L{twisted.python.failure.Failure}
        """
        if self.site.displayTracebacks:
            result = {
                'meta': {
                    "message": "Internal Error",
                    "code": 500
                },
                'data': {
                    "status": {
                        'message': str(reason),
                        'code': 500
                    }
                }
            }
        else:
            result = {
                'meta': {
                    "message": "Internal Error",
                    "code": 500
                },
                'data': {
                    "status": {
                        'message': 'Processing Failed',
                        'code': 500
                    }
                }
            }
        body = to_bytes(json.dumps(result))
        self.setResponseCode(500)
        self.setHeader(b'content-type', b"application/json")
        self.setHeader(b'content-length', intToBytes(len(body)))
        self.write(body)
        self.finish()
        return reason


Request.processingFailed = processingFailed
resource.ErrorPage = AfterShipErrorPage
resource.NoResource = AfterShipNoResource


def parse_arguments():

    def valid_setting(string):
        key, sep, value = string.partition('=')
        if not key or not sep:
            raise argparse.ArgumentTypeError(
                u'expected name=value: {}'.format(repr(string)))
        return key, value

    parser = argparse.ArgumentParser(
        description='HTTP API server for Scrapy project.')
    parser.add_argument('-p', '--port', dest='port',
                        type=int,
                        default=9080,
                        help='port number to listen on')
    parser.add_argument('-i', '--ip', dest='ip',
                        default='localhost',
                        help='IP address the server will listen on')
    parser.add_argument('--project', dest='project',
                        default='default',
                        help='project name from scrapy.cfg')
    parser.add_argument('-s', '--set', dest='set',
                        type=valid_setting,
                        action='append',
                        default=[],
                        metavar='name=value',
                        help='set/override setting (may be repeated)')
    parser.add_argument('-S', '--settings', dest='settings',
                        metavar='project.settings',
                        help='custom project settings module path')
    return parser.parse_args()


def get_application(arguments):
    ServiceRoot = load_object(settings.SERVICE_ROOT)
    site = Site(ServiceRoot())
    application = Application('scrapyrt')
    server = TCPServer(arguments.port, site, interface=arguments.ip)
    server.setServiceParent(application)
    return application


def find_scrapy_project(project):
    project_config_path = closest_scrapy_cfg()
    if not project_config_path:
        raise RuntimeError('Cannot find scrapy.cfg file')
    project_config = SafeConfigParser()
    project_config.read(project_config_path)
    try:
        project_settings = project_config.get('settings', project)
    except (NoSectionError, NoOptionError) as e:
        raise RuntimeError(e.message)
    if not project_settings:
        raise RuntimeError('Cannot find scrapy project settings')
    project_location = os.path.dirname(project_config_path)
    sys.path.append(project_location)
    return project_settings


def execute():
    sys.path.insert(0, os.getcwd())
    arguments = parse_arguments()
    if arguments.settings:
        settings.setmodule(arguments.settings)
    if arguments.set:
        for name, value in arguments.set:
            settings.set(name.upper(), value)
    settings.set('PROJECT_SETTINGS', find_scrapy_project(arguments.project))
    settings.freeze()
    setup_logging()
    application = get_application(arguments)
    app.startApplication(application, save=False)
    reactor.run()


if __name__ == '__main__':
    execute()
