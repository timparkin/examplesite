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

class Events(base.BasePage):

    @resource.GET()
    @templating.page('/event/index.html')
    def html(self, request):
        C = request.environ['couchish']
        with C.session() as S:
            page = S.doc_by_view('page/by_url',key='/events')
            events = S.docs_by_view('event/all')
        events = sorted(events,key=itemgetter('date'), reverse=True)
        sitemap = navigation.get_navigation(request)
        p = paged_list(request, events)
        return {'page': page, 'events': p['items'], 'p': Paging(request, p), 'sitemap': sitemap}

    @resource.child('${id}')
    def child(self, request, segments, id=None):
        return EventItem(id)


class EventItem(base.BasePage):

    def __init__(self, id):
        self.id = id

    @resource.GET()
    @templating.page('/event/item.html')
    def get(self, request):
        C = request.environ['couchish']                                                                
        with C.session() as S:                                                                         
            event = S.doc_by_view('event/all',key=id)                                                 
        sitemap = navigation.get_navigation(request)
        return {'event': event, 'sitemap': sitemap}                 


class Workshops(base.BasePage):


    @resource.GET()
    @templating.page('/workshop/index.html')
    def workshop_page(self, request):
        C = request.environ['couchish']
        with C.session() as S:
            results = list(S.view('page/by_url',key='/workshops',include_docs=True))
            workshops = S.docs_by_view('workshop/all')
        page = results[0].doc
        sitemap = navigation.get_navigation(request)
        p = paged_list(request, workshops)
        return {'workshops': workshops, 'p':Paging(request, p), 'page': page, 'sitemap': sitemap}

    @resource.child('{category}')
    def child(self, request, segments, category=None):
        return WorkshopCategory(category)


class WorkshopCategory(base.BasePage):


    def __init__(self, category):
        self.category = category
    
    @resource.GET()
    @templating.page('/workshop/category.html')
    def workshop_category(self, request):
        C = request.environ['couchish']
        with C.session() as S:
            results = list(S.view('page/by_url',key='/workshops',include_docs=True))
            workshops = S.docs_by_view('workshop/all')
        page = results[0].doc
        sitemap = navigation.get_navigation(request)
        p = paged_list(request, workshops)
        return {'workshops': workshops, 'p':Paging(request, p), 'page': page, 'sitemap': sitemap}

    @resource.child('{id}')
    def child(self, request, segments, id=None):
        return WorkshopItem(id)


class WorkshopItem(base.BasePage):


    def __init__(self, id):
        self.id = id

    @resource.GET()
    @templating.page('/workshop/item.html')
    def workshops(self, request):
        C = request.environ['couchish']                                                                
        with C.session() as S:                                                                         
            workshop = S.doc_by_view('workshop/all',key=self.id)                                                 
        sitemap = navigation.get_navigation(request)
        return {'workshop': workshop, 'request': request, 'sitemap': sitemap}                 
