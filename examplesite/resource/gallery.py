from __future__ import with_statement
from itertools import chain, repeat, izip
import urllib

from restish import resource, http, templating, url


from couchfti import query
from pagingish.webpaging import Paging, paged_list
from examplesite.lib import photoordering, base, photoengine, cache

import logging

log = logging.getLogger(__name__)



class Gallery(base.BasePage):

    def __init__(self, type=None):
        self.type = type

    @resource.child('{facet}')
    def facet(self, request, segments, facet=None):
        return Facet(self.type, facet)

    @resource.GET()
    @templating.page('/gallery/home.html')
    def get(self, request):
        return {}


class Facet(base.BasePage):

    def __init__(self, type, facet):
        self.type = type
        self.facet = facet

    @resource.child('{category}')
    def category(self, request, segments, category=None):
        return Category(self.type, self.facet, category)

    @resource.GET()
    @templating.page('/gallery/facet.html')
    def get(self, request):
        P = photoengine.PhotoEngine(request)
        allcategories = P.categories()
        result = {'type': self.type, 'facet': self.facet, 'category': self.category}
        result.update( {'allcategories': allcategories} )
        return result


class Category(base.BasePage):

    def __init__(self, type, facet, category):
        self.type = type
        self.facet = facet
        self.category = category

    @resource.child('{id}')
    def id(self, request, segments, id=None):
        return Item(self.type, self.facet, self.category, id)

    @resource.GET()
    @templating.page('/gallery/category.html')
    def get(self, request):
        return photoengine.get_result(self, request)


class Item(base.BasePage):

    def __init__(self, type, facet, category, id):
        self.type = type
        self.facet = facet
        self.category = category
        self.id = id

    @resource.GET()
    @templating.page('/gallery/product.html')
    def get(self, request):
        result = photoengine.get_result(self, request)
        C = request.environ['couchish']
        with C.session() as S:
            product = S.doc_by_view('product/by_code',key=self.id)
            products = S.docs_by_view('product/by_master_photo',key=product['photo']['ref'])
        result.update( {'product': product, 'products': products} )
        prev, next = photoengine.get_prev_next(product['photo']['ref'], result['opdict'])
        result.update({'prev': prev, 'next': next})
        return result








