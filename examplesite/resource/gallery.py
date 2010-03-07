from __future__ import with_statement
from itertools import chain, repeat, izip
import urllib

from restish import resource, http, templating, url


from couchfti import query
from pagingish.webpaging import Paging, paged_list
from examplesite.lib import photoordering, base, photoengine

import logging

log = logging.getLogger(__name__)

def get_parent(segments):
    if len(segments) == 1:
        return ''
    else:
        return '.'.join(segments[:-1])

def mktree(categories):
    cats = list(categories)
    cats.sort(lambda x, y: cmp(len(x['path'].split('.')), len(y['path'].split('.'))))

    last_segments_len = 1
    root = {'': {'data':('root', 'Root'), 'children':[]} }
    for c in cats:
        id = c['path']
        label = c['data']['label']
        segments = id.split('.')
        parent = get_parent(segments)
        root[id] = {'data': (id, label), 'children':[]}
        root[parent]['children'].append(root[id])
    return root['']

def get_location_categories(C):
    with C.session() as S:
        facet = S.doc_by_view('facet_location/all')
    categories = [c.__subject__ for c in facet['category']]
    return categories

def get_subject_categories(C):
    with C.session() as S:
        facet = S.doc_by_view('facet_subject/all')
    categories = [c.__subject__ for c in facet['category']]
    return categories

def get_type_categories(C):
    return [
        {'path':'print','data': {'label': 'Print'}},
        {'path':'canvas','data': {'label': 'Canvas'}},
        {'path':'greetings card','data': {'label': 'Greetings Card'}},
            ]

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
        C = request.environ['couchish']
        P = photoengine.PhotoEngine(request)
        result = P.search_products(self.facet, self.category)
        result.update( {'type': self.type, 'facet': self.facet, 'category': self.category} )
        photolist = photoordering.PhotoList()
        photolist.add(result['photos'])
        ordered_photos = photolist.process()
        p = paged_list(request, ordered_photos, max_pagesize=5)
        ordered_photos = p['items']
        result.update( {'p':Paging(request,p), 'rows': ordered_photos} )
        allcategories = P.categories()
        result.update( {'allcategories': allcategories} )
        return result
    

class Item(base.BasePage):

    def __init__(self, type, facet, category, id):
        self.type = type
        self.facet = facet
        self.category = category
        self.id = id









class Shop(resource.Resource):

    @resource.child()
    def type(self, request, segments, category=None):
        return ProductCategory('type')

    @resource.child('type/{category}')
    def type_category(self, request, segments, category=None):
        return Products('type',category)

    @resource.child()
    def subject(self, request, segments, category=None):
        return ProductCategory('subject')

    @resource.child('subject/{category}')
    def subject_category(self, request, segments, category=None):
        return Products('subject',category)

    @resource.child()
    def location(self, request, segments, category=None):
        return ProductCategory('location')

    @resource.child('location/{category}')
    def location_category(self, request, segments, category=None):
        return Products('location',category)

    @resource.child('{id}')
    def item(self, request, segments, id=None):
        return Product(id)

class _Gallery(resource.Resource):

    @resource.child('type')
    def type(self, request, segments, category=None):
        return PhotoCategory('type')

    @resource.child('type/{category}')
    def type_category(self, request, segments, category=None):
        return Photos('type',category)

    @resource.child('subject')
    def subject(self, request, segments, category=None):
        return PhotoCategory('subject')

    @resource.child('subject/{category}')
    def subject_category(self, request, segments, category=None):
        return Photos('subject',category)

    @resource.child('location')
    def location(self, request, segments, category=None):
        return PhotoCategory('location')

    @resource.child('location/{category}')
    def location_category(self, request, segments, category=None):
        return Photos('location',category)

    @resource.child('{id}')
    def item(self, request, segments, id=None):
        return Photo(id)

class ProductCategory(resource.Resource):
    
    def __init__(self, type):
        self.type = type

    @resource.GET()
    @templating.page('/shop/product-category.html')
    def GET(self, request):
        C = request.environ['couchish']
        if self.type ==  'location':
            categories = mktree(get_location_categories(C))
        if self.type == 'type':
            categories = mktree(get_type_categories(C))
        return {'request': request, 'categories': categories}
        
class Products(resource.Resource):

    def __init__(self, type, category):
        self.type = type
        self.category = category

    @resource.GET()
    @templating.page('/shop/products-list.html')
    def GET(self, request):


        C = request.environ['couchish']
        categories = mktree(get_type_categories(C))
        fields = [(self.type, self.category)]
        q = unicode(query.untokenize(('field', (name, '=', value)) for (name, value) in fields))
        cache = request.environ['cache']
        if q in cache.get['photos']:
            p = cache['photos'][q+request.GET.get('pageref',['1'])[0]]
        else:
            def search(skip=None, limit=None):
                searcher = request.environ['searcher']
                return searcher.search('product', q, skip=skip, max=limit)
            keys = search()
            keys_count = {}
            for k in keys:
                if k in keys_count:
                    keys_count[k] += 1
                else:
                    keys_count[k] = 1
            with C.session() as S:
                results_with_dupes = S.docs_by_view('product/all', keys=keys)
            photos = []
            lastid = None
            for result in results_with_dupes:
                id = result['_id']
                if id != lastid:
                    photos.append(result)
                    lastid = id
            photolist = photoordering.PhotoList()
            photolist.add(photos)
            ordered_photos = photolist.process()
            p = paged_list(request, ordered_photos, max_pagesize=5)
            cache['photos'][q+request.GET.get('pageref',['1'])[0]] = p
        ordered_photos = p['items']

        return {'p':Paging(request,p), 'rows': ordered_photos, 'request':request, 'type': self.type, 'categories': categories}

    @resource.child('{id}')
    def item(self, request, segments, id=None):
        return Product(id)


def get_categories_by_type(C, type):
    if type ==  'location':
        flatcats = get_location_categories(C)
        categories = mktree(flatcats)
    if type == 'type':
        flatcats = get_type_categories(C)
        categories = mktree(flatcats)
    if type ==  'subject':
        flatcats = get_subject_categories(C)
        categories = mktree(flatcats)
    return categories, flatcats

def get_label_by_category(flatcats, category):
    label = []
    for c in flatcats:
        path = c['path']
        if category.startswith(path):
            label.append( c['data']['label'] )
    return ', '.join(label)


def get_photos_by_category(C, type, category, filter=None):
    category_segments = category.split('.')
    product_code_lookup = {}
    if filter is None:
        startkey = category_segments
        endkey = category_segments + [{}]
        with C.session() as S:
            results_with_dupes= list(S.view('photo/by_%s_category'%type,include_docs=True,startkey=startkey,endkey=endkey))
    else:
        startkey = [filter] + category_segments
        endkey = [filter] + category_segments + [{}]
        with C.session() as S:
            results_with_dupes= list(S.view('product/by_type_and_%s_category'%type,include_docs=True,startkey=startkey,endkey=endkey))
        photo_ids = set()
        for result in results_with_dupes:
            if result.doc['photo']['_ref'] not in photo_ids:
                photo_ids.add(result.doc['photo']['_ref'])
                product_code_lookup[result.doc['photo']['_ref']] = result.doc['code']
        with C.session() as S:
            results_with_dupes= S.view('photo/all',include_docs=True,keys=list(photo_ids))
        
    photos = []
    lastid = None
    master_photos = set()
    for result in results_with_dupes:
        if result.doc['ref'] not in master_photos:
            master_photos.add(result.doc['ref'])
            result.doc['product_code'] = product_code_lookup.get(result.doc['_id'],result.doc['ref'])
            photos.append(result.doc)
    return photos

class PhotoCategory(resource.Resource):
    
    def __init__(self, type):
        self.type = type

    @resource.GET()
    @templating.page('/shop/photo-category.html')
    def GET(self, request):
        C = request.environ['couchish']
        if self.type ==  'location':
            categories = mktree(get_location_categories(C))
        if self.type == 'type':
            categories = mktree(get_type_categories(C))
        if self.type ==  'subject':
            categories = mktree(get_subject_categories(C))
        return {'request': request, 'categories': categories,'type':self.type}


class _Photos(resource.Resource):

    def __init__(self, type, category):
        self.type = type
        self.category = category

    @resource.GET()
    @templating.page('/shop/photos-list.html')
    def GET(self, request):
        C = request.environ['couchish']
        filter = request.GET.get('filter')

        if filter is None:
            categories, flatcats = get_photo_categories_by_type(C, self.type)
        else:
            categories, flatcats = get_product_categories_by_type(C, self.type, filter)

        page_title = get_label_by_category(flatcats, self.category)
        cache = request.environ['cache']
        cache_id = '%s/%s/%s/%s'%(self.type, self.category, filter, request.GET.get('pageref',['1'])[0])
        if True==False and cache_id in cache['photos']:
            p = cache['photos'][cache_id]
            allphotos = cache['allphotos'][cache_id]
        else:
            photolist = photoordering.PhotoList()
            allphotos = get_photos_by_category(C, self.type, self.category, filter)
            photolist.add(allphotos)
            photos = photolist.process()
            p = paged_list(request, photos, max_pagesize=5)
            cache['photos'][cache_id] = p
            cache['allphotos'][cache_id] = allphotos

        return {'p':Paging(request,p), 'rows': p['items'], 'num_photos': len(allphotos),  'request':request, 'type': self.type, 'categories': categories, 'page_title': page_title}

    @resource.child('{id}')
    def item(self, request, segments, id=None):
        return Photo(id, self.type, self.category)


class Product(resource.Resource):

    def __init__(self, id):
        self.id = id.replace('|','/')

    @resource.GET()
    @templating.page('/shop/product.html')
    def GET(self, request):
        C = request.environ['couchish']
        with C.session() as S:
            product = S.doc_by_view('product/by_code',key=self.id)
            products = S.docs_by_view('product/by_master_photo',key=product['photo']['ref'])
        #if product['type'] == 'Print' or product['type'] == 'Canvas':
        #    product = product.__subject__
        #    product['pricing'] = pricing.get_options(product)

        zoom = request.GET.get('zoom') == 'True'
        products = list(products)
        return {'product':product,
                'zoom':zoom,
                'request':request,
                'products':products}

       
class PhotoRedirect(resource.Resource):

    def __init__(self, ref):
        self.ref = ref

    @resource.GET()
    def GET(self, request):
        C = request.environ['couchish']
        with C.session() as S:
            photo = S.doc_by_view('photo/by_code',key=self.ref)
        u = url.URL('/photos').child('location').child(photo['location_category'][-1]['path']).child(photo['ref'])
        return http.see_other(u)

        
class Photo(resource.Resource):

    def __init__(self, id, type, category):
        self.id = id.replace('|','/')
        self.type = type
        self.category = category

    @resource.GET()
    @templating.page('/shop/photo.html')
    def GET(self, request):
        C = request.environ['couchish']

        with C.session() as S:
            product = S.doc_by_view('photo/by_code',key=self.id)
            products = list(S.docs_by_view('product/by_master_photo',key=product['ref']))

        filter = request.GET.get('filter')
        photolist = photoordering.PhotoList()
        photolist.add(get_photos_by_category(C, self.type, self.category, filter))
        photos = photolist.process()

        refs = []
        for row in photos:
            for item in row:
                refs.append(item.photo['ref'])
        prev = None
        next = None
        num_items = len(refs)
        for n, ref in enumerate(refs):
            if ref == self.id:
                if n+1<num_items:
                    next = refs[n+1]
                break
            prev = ref

        zoom = request.GET.get('zoom') == 'True'
        products = list(products)
        products.sort(lambda x,y: cmp(y['type'],x['type']))
        return {'photo':product,
                'zoom':zoom,
                'request':request,
                'products':products,
                'prev': prev,
                'next': next}
