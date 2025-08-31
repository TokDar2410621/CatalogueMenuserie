from collections import namedtuple
from django.test import TestCase, RequestFactory
from unittest.mock import patch

from pages.models import CataloguePage


FakeBlock = namedtuple("FakeBlock", ["block_type", "value"])


class CataloguePagePriceFilterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _serve(self, page, query_string=""):
        request = self.factory.get("/", data=None)
        if query_string:
            request = self.factory.get(f"/?{query_string}")
        with patch("pages.models.render") as mocked_render:
            page.serve(request)
            # render(request, template, context)
            ctx = mocked_render.call_args[0][2]
        return ctx["items"]

    def test_invalid_item_price_excluded(self):
        page = CataloguePage(title="test", slug="test")
        page.__dict__["contenu"] = [FakeBlock("item", {"titre": "X", "prix": "oops"})]
        items = self._serve(page, "min=0")
        self.assertEqual(items, [])

    def test_invalid_filter_ignored(self):
        page = CataloguePage(title="test", slug="test")
        page.__dict__["contenu"] = [FakeBlock("item", {"titre": "X", "prix": 10})]
        items = self._serve(page, "min=bad&max=also_bad")
        self.assertEqual(items, page.__dict__["contenu"])
