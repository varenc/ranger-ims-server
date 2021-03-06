"""
Tests for :mod:`ranger-ims-server.ext.klein`
"""

from klein.test.test_resource import Klein, requestMock

from twisted.web.iweb import IRequest

from ..klein import KleinRenderable, static
from ..trial import TestCase


__all__ = ()



class StaticDecoratorTests(TestCase):
    """
    Tests for :func:`static`
    """

    class Application(object):
        router = Klein()

        hello = "Hello"

        @router.route("/")
        @static
        def root(self, request: IRequest) -> KleinRenderable:
            return self.hello


    def test_static_entity(self) -> None:
        """
        :func:`static` returns the entity returned by the wrapped method.
        """
        app = self.Application()
        request = requestMock(b"/")

        entity = app.root(request)

        self.assertIdentical(entity, app.hello)


    def test_static_etag(self) -> None:
        """
        :func:`static` sets an ``ETag`` header.
        """
        app = self.Application()
        request = requestMock(b"/")

        app.root(request)

        etags = request.responseHeaders.getRawHeaders("etag")
        self.assertTrue(len(etags) == 1, etags)
        etag = etags[0]
        self.assertTrue(etag)


    def test_static_cacheControl(self) -> None:
        """
        :func:`static` sets a ``Cache-Control`` header.
        """
        app = self.Application()
        request = requestMock(b"/")

        app.root(request)

        etags = request.responseHeaders.getRawHeaders("cache-control")
        self.assertTrue(len(etags) == 1, etags)
        etag = etags[0]
        self.assertTrue(etag)
