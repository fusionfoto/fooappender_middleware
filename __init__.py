from swift.common.utils import split_path, get_logger
from webob import Request
from webob.exc import HTTPBadRequest, HTTPServerError
import re
from swift.proxy.controllers.base import get_container_info,get_object_info

# Example Swift middleware: fooappender_middleware
# This example intercepts all PUT and POST requests to objects in a swift cluster whose name matches the configured regex, and, usefully, appends a metadata keyval foo:bar to them.
# straill (SwiftStack) 2017/10/19.
# Supplied, as example code, on an as-is basis.
class FooAppenderMiddleware(object):
    def __init__(self, app, conf):
        self.app = app
        self.logger = get_logger(conf, log_route='fooappender_middleware')

        # The value doesn't have to be bar: allow it to be configurable, from our middleware (paste) config.
        # The default is 'bar'.
        self.bar = conf.get('bar', 'bar');
        # A regular expression. If this matches the full object path (account/container/object)
        # then we enforce metadata validity for this PUT or POST.
        self.enforce_pattern = conf.get('enforce_pattern', '')
        self.enforce_pattern_re = re.compile(self.enforce_pattern)
        
    # Main middleware starts here.
    def __call__(self, env, start_response):
        req = Request(env)

        # We don't want to block request we don't care about, so befre doing anything else we do everything we can 
        # to allow thoese reqeusts we *don't* care about further on up the middleware pipeline.

        # We only care about PUT and POST requests.
        if env['REQUEST_METHOD'] not in ['PUT','POST']:
            return self.app(env, start_response)

        version, account, container, obj = split_path(
            env['PATH_INFO'], 1, 4, True)
 
        # I've left the logging at /info for demo purposes, but you'll probably want to tone it down. Or remove it.
        self.logger.info("fooappender_middleware: looks like we're uploading %s/%s/%s" % ( account, container, obj ))

        # Check there is an object component; we don't want this request if it pertain to an account or container, for example.
        if not obj:
          return self.app(env, start_response)

        self.logger.info("fooappender_middleware: looks like we're uploading an object, so I might be interested")

        # Chec our account/container/object regex. If we're not supposed to enforce metadata on this request, allow it to pass through.
        self.logger.info("fooappender_middleware: enforce pattern is %s " % self.enforce_pattern)
        if not self.enforce_pattern_re.search("%s/%s/%s" % (account,container,obj)):
          return self.app(env, start_response)

        self.logger.info("fooappender_middleware: looks like we're uploading or modifying an object, at a path I'm supposed to manage. Appending our foo keyval to the object metadata.")

        # Add our foo:bar user metadata to the object.
        req.headers['x-object-meta-foo'] = self.bar

        # Allow the request to continue.
        return self.app(env, start_response)

def my_filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def fooappender_middleware(app):
        return FooAppenderMiddleware(app, conf)

    return fooappender_middleware
