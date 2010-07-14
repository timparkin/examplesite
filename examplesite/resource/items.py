from __future__ import with_statement
import logging
from restish import http, resource, templating
from menuish.menu import create_sitemap

from operator import itemgetter
from pagingish.webpaging import Paging, paged_list

from datetime import date

from examplesite.resource import navigation
from examplesite.lib import base

log = logging.getLogger(__name__)



class News(base.BasePage):


    @resource.GET()
    @templating.page('/news/index.html')
    def html(self, request):
        C = request.environ['couchish']
        with C.session() as S:
            page = S.doc_by_view('page/by_url',key='/news')
            newsitems = S.docs_by_view('newsitem/all')
        newsitems = sorted(newsitems,key=itemgetter('date'), reverse=True)
        newsitems = [n for n in newsitems if n['date'] < date.today()]
        sitemap = navigation.get_navigation(request)
        p = paged_list(request, newsitems)
        return {'page': page, 'newsitems': p['items'], 'p': Paging(request, p), 'sitemap': sitemap}

    @resource.child('{id}')
    def child(self, request, segments, id=None):
        return NewsItem(id)

class NewsItem(base.BasePage):

    def __init__(self, id):
        self.id = id

    @resource.GET()
    @templating.page('/news/item.html')
    def get(self, request):
        C = request.environ['couchish']
        with C.session() as S:
            newsitem = S.doc_by_view('newsitem/all',key=self.id)
        sitemap = navigation.get_navigation(request)
        return {'newsitem': newsitem, 'sitemap': sitemap}

