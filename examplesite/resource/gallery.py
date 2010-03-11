from __future__ import with_statement
from itertools import chain, repeat, izip
import urllib

from restish import resource, http, templating, url


from couchfti import query
from pagingish.webpaging import Paging, paged_list
from examplesite.lib import photoordering, base, photoengine, cache

import logging

log = logging.getLogger(__name__)

def get_result(self, request):
    cache_db = request.environ['cache']
    cache_id = cache.key('photos',self.type, self.facet, self.category)
    cache_result = cache_db.get(cache_id)
    P = photoengine.PhotoEngine(request)
    if cache_result:
        result = cache_result['data']
    else:
        result = P.search_products(self.facet, self.category)
        result.update( {'type': self.type, 'facet': self.facet, 'category': self.category} )
        photolist = photoordering.PhotoList()
        photolist.add(result['photos'])
        ordered_photos = photolist.process()
        result['opdict'] = [[p.photodict for p in row] for row in ordered_photos]
        cache_db.update( [ {'_id': cache_id, 'data': result} ] )
    p = paged_list(request, result['opdict'], max_pagesize=5)
    page_of_ordered_photos = p['items']
    result.update( {'p':Paging(request,p), 'rows': page_of_ordered_photos} )
    allcategories = P.categories()
    result.update( {'allcategories': allcategories} )
    
    return result

def get_prev_next(id, rows):
    prev = next = None
    all_photos = []
    for row in rows:
        for p in row:
            all_photos.append(p)
    for n,p in enumerate(all_photos):
        if p['ref'] == id:
            if n-1 >= 0:
                prev = all_photos[n-1]['code']
            if n+1 < len(rows):
                next = all_photos[n+1]['code']
    return prev, next

class Gallery(base.BasePage):

    def __init__(self, type):
        self.type = type

    @resource.child('{facet}')
    def facet(self, request, segments, facet=None):
        return Facet(self.type, facet)


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
        return get_result(self, request)
   

class Item(base.BasePage):

    def __init__(self, type, facet, category, id):
        self.type = type
        self.facet = facet
        self.category = category
        self.id = id

    @resource.GET()
    @templating.page('/gallery/product.html')
    def get(self, request):
        result = get_result(self, request)
        C = request.environ['couchish']
        with C.session() as S:
            product = S.doc_by_view('product/by_code',key=self.id)
            products = S.docs_by_view('product/by_master_photo',key=product['photo']['ref'])
        result.update( {'product': product, 'products': products} )
        prev, next = get_prev_next(product['photo']['ref'], result['opdict'])
        result.update({'prev': prev, 'next': next})
        return result








