from couchfti import query
from examplesite.lib.categories import mktree


class PhotoEngine(object):

    def __init__(self, request):
        e = request.environ
        self.searcher = e['searcher']
        self.couchish = e['couchish']

    def search(self, type, fields=None):
        if fields:
            with self.couchish.session() as S:
                docs = S.view('%s/all'%type)
            print 'D',docs
            keys = [d.key for d in docs]
        else:
            q = unicode(query.untokenize(('field', (name, '=', value)) for (name, value) in fields))
            results = self.searcher.search(type, q, 0, 10000)
            keys = [r.id for r in results]
        if type == 'product':
            return self.products_from_keys(keys)
        if type == 'photo':
            return photos_from_keys(keys)

    def all_keys(self):
        with C.session() as S:
            docs = S.docs_by_view('photo/all')

    def categories(self, type, fields):
        top_level_fields = []
        for field in fields:
            if field[0] == 'location' or field[0] == 'subject':
                continue
            top_level_fields.append(field)
        results = self.search(type, top_level_fields)
        return results['categories']

    def products_from_keys(self, product_keys):
        with self.couchish.session() as S:
            products = S.docs_by_view('product/all',keys=product_keys)
        products_by_photo = {}
        products = list(products)
        for product in products:
            products_by_photo.setdefault(product['photo']['_ref'],[]).append(product)
        photo_keys = products_by_photo.keys()
        with self.couchish.session() as S:
            photos = S.docs_by_view('photo/all',keys=photo_keys)
        location_categories = {}
        subject_categories = {}
        photos = list(photos)
        for photo in photos:
            for category in photo['location_category']:
                location_categories[ category['path'] ] = category
            for category in photo['subject_category']:
                subject_categories[ category['path'] ] = category
        categories = {}
        categories['location'] = {'flatcats': location_categories, 'tree': mktree(location_categories.values())}
        categories['subject'] = {'flatcats': subject_categories, 'tree': mktree(subject_categories.values())}
        return {'products': products, 'photos': photos, 'products_by_photo': products_by_photo, 'categories': categories }
        
        


        
            



