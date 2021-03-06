from couchfti import query
from examplesite.lib.categories import mktree
from examplesite.lib import cache

def unwrap_doc(doc):
    if hasattr(doc, '__subject__'):
        return doc.__subject__
    return doc

def unwrap_docs(docs):
    out = []
    for doc in docs:
        out.append(doc)
    return out

def _dictify_photo(photo):
    p = photo['photo']
    out = {}
    out['metadata'] = p.metadata
    out['filename'] = p.filename
    out['id'] = p.id
    out['doc_id'] = p.doc_id
    photo['photo'] = out
    return unwrap_doc(photo)

class PhotoEngine(object):

    def __init__(self, request):
        e = request.environ
        self.cache = e['cache']
        self.searcher = e['searcher']
        self.couchish = e['couchish']
        self.type = request.GET.get('filter')

    def search_products(self, facet, category):
        return self._photos_from_products(self._search_products(facet, category))

    def _search_products(self, facet, category):
        # Use an appropriate couch search to get all of the products that match the filters.. 
        # returns a couchdb result set
        if category:
            category_segments = category.split('.')
        if self.type is None:
            if facet is None:
                print 'no facet for type'
                with self.couchish.session() as S:
                    results_with_dupes=unwrap_docs(S.view('product/all', include_docs=True))
            else:
                print 'facet only'
                startkey = category_segments
                endkey = category_segments + [{}]
                with self.couchish.session() as S:
                    results_with_dupes=unwrap_docs(S.view('product/by_%s_category'%facet,include_docs=True,startkey=startkey,endkey=endkey))
        else:
            if facet is None:
                print 'type only'
                startkey = [self.type] 
                endkey = [self.type] + [{}]
                with self.couchish.session() as S:
                    results_with_dupes= unwrap_docs(S.view('product/by_type_and_location_category',include_docs=True,startkey=startkey,endkey=endkey))
            else:
                print 'type and facet'
                startkey = [self.type] + category_segments
                endkey = [self.type] + category_segments + [{}]
                with self.couchish.session() as S:
                    results_with_dupes= unwrap_docs(S.view('product/by_type_and_%s_category'%facet,include_docs=True,startkey=startkey,endkey=endkey))
        return results_with_dupes

    def _photos_from_products(self, results_with_dupes):
        products_by_photo = {}
        photo_ids = set()
        # From the list of products, build a unique set in 'photo_ids'
        # also create an index from photo code to product
        for result in results_with_dupes:
            if result.doc['photo']['_ref'] not in photo_ids:
                photo_ids.add(result.doc['photo']['_ref'])
                products_by_photo[result.doc['photo']['_ref']] = result.doc['code']
        
        # Build a list of unique photos which include a key 'product_code' to point to original product
        with self.couchish.session() as S:
            results_with_dupes= S.view('photo/all',include_docs=True,keys=list(photo_ids))
        photos = []
        lastid = None
        master_photos = set()
        for result in results_with_dupes:
            if result.doc['code'] not in master_photos:
                master_photos.add(result.doc['code'])
                result.doc['product_code'] = products_by_photo.get(result.doc['_id'],result.doc['code'])
                photos.append(_dictify_photo(result.doc))

        # Build the categories covered by these photos
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
        return {'photos': photos, 'products_by_photo': products_by_photo, 'categories': categories }


    def categories(self):
        result = self.cache.get(cache.key('categories',self.type ))
        if result:
            return result['data']
        if self.type:
            startkey = [self.type]
            endkey = [self.type] + [{}]
            with self.couchish.session() as S:
                results= list(S.view('product/by_type_with_categories',startkey=startkey,endkey=endkey))
        else:
            with self.couchish.session() as S:
                results= list(S.view('product/by_type_with_categories'))
        all_categories = {'location':{}, 'subject': {}}
        for result in results:
            facet = result.value['facet']
            category = result.value['category']
            all_categories[facet][category['path']] = category
        with self.couchish.session() as S:
            location_categories= S.doc_by_view('facet_location/all')['category']
        with self.couchish.session() as S:
            subject_categories= S.doc_by_view('facet_subject/all')['category']
        all_sorted_categories = {'location':[], 'subject': []}
        for category in location_categories:
            if category['path'] in all_categories['location']:
                all_sorted_categories['location'].append( all_categories['location'][category['path']] )
        for category in subject_categories:
            if category['path'] in all_categories['subject']:
                all_sorted_categories['subject'].append( all_categories['subject'][category['path']] )
        categories = {'_id': cache.key('categories',self.type), 'data': {}}
        categories['data']['location'] = {'flatcats': all_sorted_categories['location'], 'tree': mktree(all_sorted_categories['location'])}
        categories['data']['subject'] = {'flatcats': all_sorted_categories['subject'], 'tree': mktree(all_sorted_categories['subject'])}
        self.cache.update([categories])
        return categories['data']

        


        
            



