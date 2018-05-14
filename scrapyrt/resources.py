# -*- coding: utf-8 -*-
import os

import demjson
from scrapy.utils.misc import load_object
from scrapy.utils.serialize import ScrapyJSONEncoder
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure
from twisted.web import resource, server
from twisted.web.error import Error, UnsupportedMethod

from . import log
from .conf import settings
from .utils import extract_scrapy_request_args, to_bytes
from .utils import extract_api_params_from_request
from .utils import extract_api_headers

from jsonschema import validate
from jsonschema.exceptions import ValidationError


REQUEST_SCHEMA = None
request_schema_file = os.getenv('REQUEST_SCHEMA_FILE',
                                "../settings/schemas/request_schema.json")

if os.path.isfile(request_schema_file):
    with open(request_schema_file) as f:
        REQUEST_SCHEMA = demjson.decode(f.read())

AFTERSHIP_COURIER_API_KEY = os.getenv("AFTERSHIP_COURIER_API_KEY")
if AFTERSHIP_COURIER_API_KEY is None:
    raise KeyError('should set env var `AFTERSHIP_COURIER_API_KEY`')

# XXX super() calls won't work wihout object mixin in Python 2
# maybe this can be removed at some point?


class ServiceResource(resource.Resource, object):
    json_encoder = ScrapyJSONEncoder()

    def __init__(self, root=None):
        resource.Resource.__init__(self)
        self.root = root

    def render(self, request):
        try:
            result = resource.Resource.render(self, request)
        except Exception as e:
            result = self.handle_error(e, request)

        if not isinstance(result, Deferred):
            return self.render_object(result, request)

        # deferred result - add appropriate callbacks and errbacks
        result.addErrback(self.handle_error, request)

        def finish_request(obj):
            request.write(self.render_object(obj, request))
            request.finish()

        result.addCallback(finish_request)
        return server.NOT_DONE_YET

    def handle_error(self, exception_or_failure, request):
        """Override this method to add custom exception handling.

        :param request: twisted.web.server.Request
        :param exception_or_failure: Exception or
            twisted.python.failure.Failure
        :return: dict which will be converted to JSON error response

        """
        failure = None
        if isinstance(exception_or_failure, Exception):
            exception = exception_or_failure
        elif isinstance(exception_or_failure, Failure):
            exception = exception_or_failure.value
            failure = exception_or_failure
        else:
            raise TypeError(
                'Expected Exception or {} instances, got {}'.format(
                    Failure,
                    exception_or_failure.__class__
                ))
        if request.code == 200:
            # Default code - means that error wasn't handled
            if isinstance(exception, UnsupportedMethod):
                request.setResponseCode(405)
            elif isinstance(exception, Error):
                code = int(exception.status)
                if code == 4001 or code == 4002:
                    code = 400
                request.setResponseCode(code)
            else:
                request.setResponseCode(500)
                if not hasattr(exception, 'status'):
                    setattr(exception, 'status', '500')
            if request.code == 500:
                log.logger.error(failure)
        return self.format_error_response(exception, request)

    def format_error_response(self, exception, request):
        # Python exceptions don't have message attribute in Python 3+ anymore.
        # Twisted HTTP Error objects still have 'message' attribute even in 3+
        # and they fail on str(exception) call.
        api_params = extract_api_params_from_request(request)

        if hasattr(exception, 'message'):
            msg = exception.message
        else:
            msg = str(exception)
        if request.code == 415:
            api_params = {}
        elif request.code == 500:
            msg = 'Internal error'
        if exception.status == '400':
            api_params = {}
        result = {
            "meta": {
                "message": msg,
                "code": int(exception.status)
            },
            "data": api_params
        }
        log.logger.error(result)
        return result

    def render_object(self, obj, request):
        r = self.json_encoder.encode(obj) + "\n"
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods',
                          ', '.join(getattr(self, 'allowedMethods', [])))
        request.setHeader('Access-Control-Allow-Headers', 'X-Requested-With')
        request.setHeader('Content-Length', len(r))
        return r.encode("utf8")


class RealtimeApi(ServiceResource):

    def __init__(self, **kwargs):
        super(RealtimeApi, self).__init__(self)
        for route, resource_path in settings.RESOURCES.items():
            resource_cls = load_object(resource_path)
            route = to_bytes(route)
            self.putChild(route, resource_cls(self, **kwargs))


class CrawlResource(ServiceResource):

    isLeaf = True
    allowedMethods = ['GET', 'POST']

    def render_GET(self, request, **kwargs):
        """Request querysting must contain following keys: url, spider_name.

        At the moment kwargs for scrapy request are not supported in GET.
        They are supported in POST handler.
        """
        request.setResponseCode(200)
        response = {
            "meta": {
                "message": "OK",
                "code": 200
            },
            "data": {}
        }
        return response

    def render_POST(self, request, **kwargs):
        """
        :param request:
            body should contain JSON

        Required keys in JSON posted:

        :spider_name: string
            name of spider to be scheduled.

        :request: json object
            request to be scheduled with spider.
            Note: request must contain url for spider.
            It may contain kwargs to scrapy request.

        """
        api_key = request.getHeader('aftership-courier-api-key')
        content_type = request.getHeader('content-type')
        api_headers = extract_api_headers(request)
        api_params = extract_api_params_from_request(request)

        log_msg = {'api_headers': api_headers, 'api_params': api_params}

        if api_params is None:
            log.logger.error(log_msg)
            raise Error('413', 'Payload too large')

        if api_key is None or api_key != AFTERSHIP_COURIER_API_KEY:
            log.logger.error(log_msg)
            raise Error('403', message='Invalid API key')

        if content_type is None or content_type != 'application/json':
            log.logger.error(log_msg)
            raise Error('415', message='Unsupported media type')

        if isinstance(api_params, str):
            log.logger.error(log_msg)
            raise Error('400', message='Invalid JSON')

        try:
            validate(api_params, REQUEST_SCHEMA)
        except ValidationError:
            log.logger.error(log_msg)
            raise Error('4001', "Invalid payload")

        log.logger.info(log_msg)

        self.slug = api_params.get('slug')
        api_params = self.wrap_aftership_courier_api(api_params)

        scrapy_request_args = extract_scrapy_request_args(
            api_params.get("request", {}), raise_error=True)

        return self.prepare_crawl(api_params, scrapy_request_args, **kwargs)

    def wrap_aftership_courier_api(self, api_params):
        spider_name = api_params.get('slug') + 'spider'
        # print('spider_name: {}'.format(spider_name))
        start_requests = True
        request = {
            'meta': api_params,
            'dont_filter': True
        }
        return {
            'request': request,
            'start_requests': start_requests,
            'spider_name': spider_name
        }

    def get_required_argument(self, api_params, name, error_msg=None):
        """Get required API key from dict-like object.

        :param dict api_params:
            dictionary with names and values of parameters supplied to API.
        :param str name:
            required key that must be found in api_params
        :return: value of required param
        :raises Error: Bad Request response

        """
        if error_msg is None:
            error_msg = 'Missing required parameter: {}'.format(repr(name))
        try:
            value = api_params[name]
        except KeyError:
            raise Error('400', message=error_msg)
        if not value:
            raise Error('400', message=error_msg)
        return value

    def prepare_crawl(self, api_params, scrapy_request_args, *args, **kwargs):
        """Schedule given spider with CrawlManager.

        :param dict api_params:
            arguments needed to find spider and set proper api parameters
            for crawl (max_requests for example)

        :param dict scrapy_request_args:
            should contain positional and keyword arguments for Scrapy
            Request object that will be created
        """
        spider_name = self.get_required_argument(api_params, 'spider_name')
        start_requests = api_params.get("start_requests", False)

        dfd = self.run_crawl(
            spider_name, scrapy_request_args, max_requests=None,
            start_requests=start_requests, *args, **kwargs)
        dfd.addCallback(
            self.prepare_response, request_data=api_params, *args, **kwargs)
        return dfd

    def run_crawl(self, spider_name, scrapy_request_args,
                  max_requests=None, start_requests=False, *args, **kwargs):
        crawl_manager_cls = load_object(settings.CRAWL_MANAGER)
        manager = crawl_manager_cls(spider_name,
                                    scrapy_request_args,
                                    max_requests,
                                    start_requests=start_requests)
        kwargs.update(scrapy_request_args.get('meta'))
        dfd = manager.crawl(*args, **kwargs)
        return dfd

    def prepare_response(self, result, *args, **kwargs):
        items = result.get("items")
        response = {
            "meta": {
                "message": "OK",
                "code": 200
            },
            "data": {
                "trackings": items
            }
        }

        errors = result.get("errors")
        if errors:
            raise Error('500', 'Internal error')
        return response
