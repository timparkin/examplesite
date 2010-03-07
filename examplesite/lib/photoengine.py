from couchfti import query
from examplesite.lib.categories import mktree


class PhotoEngine(object):

    def __init__(self, request):
        e = request.environ
        self.searcher = e['searcher']
        self.couchish = e['couchish']
        self.type = request.GET.get('filter')

    def search_products(self, facet, category):
        return self._photos_from_products(self._search_products(facet, category))

    def _search_products(self, facet, category):
        if category:
            category_segments = category.split('.')
        if self.type is None:
            if facet is None:
                print 'no facet for type'
                with self.couchish.session() as S:
                    results_with_dupes=list(S.view('product/all', include_docs=True))
            else:
                print 'facet only'
                startkey = category_segments
                endkey = category_segments + [{}]
                with self.couchish.session() as S:
                    results_with_dupes=list(S.view('product/by_%s_category'%facet,include_docs=True,startkey=startkey,endkey=endkey))
        else:
            if facet is None:
                print 'type only'
                startkey = [self.type] 
                endkey = [self.type] + [{}]
                with self.couchish.session() as S:
                    results_with_dupes= list(S.view('product/by_type',include_docs=True,startkey=startkey,endkey=endkey))
            else:
                print 'type and facet'
                startkey = [self.type] + category_segments
                endkey = [self.type] + category_segments + [{}]
                with self.couchish.session() as S:
                    results_with_dupes= list(S.view('product/by_type_and_%s_category'%facet,include_docs=True,startkey=startkey,endkey=endkey))
        return results_with_dupes

    def _photos_from_products(self, results_with_dupes):
        products_by_photo = {}
        photo_ids = set()
        for result in results_with_dupes:
            if result.doc['photo']['_ref'] not in photo_ids:
                photo_ids.add(result.doc['photo']['_ref'])
                products_by_photo[result.doc['photo']['_ref']] = result.doc['code']
        with self.couchish.session() as S:
            results_with_dupes= S.view('photo/all',include_docs=True,keys=list(photo_ids))
        photos = []
        lastid = None
        master_photos = set()
        for result in results_with_dupes:
            if result.doc['code'] not in master_photos:
                master_photos.add(result.doc['code'])
                result.doc['product_code'] = products_by_photo.get(result.doc['_id'],result.doc['code'])
                photos.append(result.doc)
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
        categories = {}
        categories['location'] = {'flatcats': all_sorted_categories['location'], 'tree': mktree(all_sorted_categories['location'])}
        categories['subject'] = {'flatcats': all_sorted_categories['subject'], 'tree': mktree(all_sorted_categories['subject'])}
        return categories

        


        
            



