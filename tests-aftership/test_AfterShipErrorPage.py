from twisted.trial.unittest import TestCase
from scrapyrt.cmdline import (AfterShipErrorPage, AfterShipNoResource, processingFailed)
from scrapyrt.utils import to_bytes
from twisted.web.resource import (
    NOT_FOUND, FORBIDDEN, Resource, ErrorPage, NoResource, ForbiddenResource,
    getChildForRequest)
from twisted.web.test.requesthelper import DummyRequest
from mockito import mock, when
import json

class AfterShipErrorPageTests(TestCase):
    """
    Tests for L{ErrorPage}, L{NoResource}, and L{ForbiddenResource}.
    """

    errorPage = AfterShipErrorPage
    noResource = AfterShipNoResource
    forbiddenResource = ForbiddenResource

    def test_getChild(self):
        """
        The C{getChild} method of L{ErrorPage} returns the L{ErrorPage} it is
        called on.
        """
        page = self.errorPage(404, "Not found", "Not found")
        self.assertIdentical(page.getChild(b"name", object()), page)

    def _pageRenderingTest(self, page, code, brief, detail):
        request = DummyRequest([b''])

        content = mock()
        when(content).getvalue().thenReturn('{"slug": "yunexpress","tracking_queries": [{"tracking_number": "YT1802927571800445"}]}')
        request.content = content

        expected = {
            "meta": {
                "message": brief,
                "code": code
            },
            "data": detail
        }

        self.assertEqual(page.render(request), to_bytes(json.dumps(expected)))
        self.assertEqual(request.responseCode, code)


    def test_errorPageRendering(self):
        """
        L{ErrorPage.render} returns a C{bytes} describing the error defined by
        the response code and message passed to L{ErrorPage.__init__}.  It also
        uses that response code to set the response code on the L{Request}
        passed in.
        """
        code = 404
        brief = "Not found"
        detail = {"slug": "yunexpress","tracking_queries": [{"tracking_number": "YT1802927571800445"}]}
        page = self.errorPage(code, brief, detail)
        self._pageRenderingTest(page, code, brief, detail)