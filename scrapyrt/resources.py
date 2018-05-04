# -*- coding: utf-8 -*-
import os
import copy

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

from jsonschema import validate
from jsonschema.exceptions import ValidationError


REQUEST_SCHEMA = None
request_schema_file = os.getenv('REQUEST_SCHEMA_FILE',
                               "../settings/schemas/request_schema.json")

if os.path.isfile(request_schema_file):
    with open(request_schema_file) as f:
        REQUEST_SCHEMA = demjson.decode(f.read())

AFTERSHIP_API_KEY = os.getenv("AFTERSHIP_API_KEY")
if not AFTERSHIP_API_KEY:
    raise KeyError('should set env var AFTERSHIP_API_KEY')

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
                if code == 4001:
                    code = 400
                request.setResponseCode(code)
            else:
                request.setResponseCode(500)
            if request.code == 500:
                log.err(failure)
        return self.format_error_response(exception, request)

    def format_error_response(self, exception, request):
        # Python exceptions don't have message attribute in Python 3+ anymore.
        # Twisted HTTP Error objects still have 'message' attribute even in 3+
        # and they fail on str(exception) call.
        request_body = request.content.getvalue()
        try:
            api_params = demjson.decode(request_body)
        except demjson.JSONDecodeError:
            api_params = {}
        if hasattr(exception, 'message'):
            msg = exception.message
        else:
            msg = str(exception)
        if request.code == 500:
            msg = 'Internal error'
        return {
            "meta": {
                "message": msg,
                "code": int(exception.status)
            },
            "data": api_params
        }

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
        aftership_api_key = request.getHeader('aftership-api-key')
        if aftership_api_key is None or aftership_api_key != AFTERSHIP_API_KEY:
            raise Error('403', message='Invalid API key')
        request_body = request.content.getvalue()
        try:
            api_params = demjson.decode(request_body)
        except demjson.JSONDecodeError:
            raise Error('400', message='Invalid JSON')

        log.msg("{}".format(api_params))

        self.valid_aftership_courier_api_params(api_params)
        self.slug = api_params.get('slug')
        api_params = self.wrap_aftership_courier_api(api_params)

        if api_params.get("start_requests"):
            # start requests passed so 'request' argument is optional
            _request = api_params.get("request", {})
        else:
            # no start_requests, 'request' is required
            _request = self.get_required_argument(api_params, "request")
        try:
            scrapy_request_args = extract_scrapy_request_args(
                _request, raise_error=True
            )
        except ValueError as e:
            raise Error('400', str(e))

        self.validate_options(scrapy_request_args, api_params)
        return self.prepare_crawl(api_params, scrapy_request_args, **kwargs)

    def valid_aftership_courier_api_params(self, api_params):
        try:
            validate(api_params, REQUEST_SCHEMA)
        except ValidationError:
            raise Error('4001', "Invalid payload")

    def wrap_aftership_courier_api(self, api_params):
        spider_name = api_params.get('slug') + 'spider'
        # print('spider_name: {}'.format(spider_name))
        start_requests = True
        request = {
            'meta': copy.deepcopy(api_params),
            'dont_filter': True
        }
        aftership_api_params = {
            'request': request,
            'start_requests': start_requests,
            'spider_name': spider_name
        }
        return aftership_api_params

    def validate_options(self, scrapy_request_args, api_params):
        url = scrapy_request_args.get("url")
        start_requests = api_params.get("start_requests")
        if not url and not start_requests:
            raise Error('400',
                        "'url' is required if start_requests are disabled")

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
        try:
            max_requests = api_params['max_requests']
        except (KeyError, IndexError):
            max_requests = None
        dfd = self.run_crawl(
            spider_name, scrapy_request_args, max_requests,
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
            response["errors"] = errors
        return response
