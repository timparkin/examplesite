from datetime import date

from menuish.menu import create_sitemap
from operator import itemgetter




WORKSHOP_CATEGORIES = [('practical','Practical Workshops'),('software','Software Training'),('capture2computer', 'Capture 2 Computer')]



def get_workshop_nodes(C):

    with C.session() as S:
        workshops = S.docs_by_view('workshop/all')
    nodes = []
    workshops = sorted(workshops,key=itemgetter('from_date'))
    for category in WORKSHOP_CATEGORIES:
        nodes.append( ['root.workshops.%s'%category[0],category[1], 1, {}] )
        for workshop in [w for w in workshops if w.get('category') == category[0]]:
            nodes.append( ['root.workshops.%s.%s'%(category[0],workshop['_id']),workshop['menu_title'], 1, {}] )
    return nodes

def get_news_nodes(C):
    with C.session() as S:
        newsitems = S.docs_by_view('newsitem/all')
    newsitems = sorted(newsitems,key=itemgetter('date'), reverse=True)
    nodes = []
    for newsitem in newsitems:
        if newsitem['date'] < date.today():
            nodes.append( ['root.news.%s'%newsitem['_id'],newsitem['menu_title'], 1, {}] )
    return nodes

def get_events_nodes(C):
    with C.session() as S:
        events = S.docs_by_view('event/all')
    events = sorted(events,key=itemgetter('date'), reverse=True)
    nodes = []
    for event in events:
        nodes.append( ['root.events.%s'%event['_id'],event['menu_title'], 1, {}] )
    return nodes

def get_navigation(request):
    segments = request.url.path_segments
    C = request.environ['couchish']
    with C.session() as S:
        pages = list(S.view('page/by_segments'))
    count = 0
    lastparent = []
    sitemap = []
    for page in pages:
        if page.key != [""]:
            key = 'root.' + '.'.join(page.key)
        else:
            key = 'root'
        parent = key.split('.')[:-1]
        if parent == lastparent:
            count += 1
        else:
            count = 1
            lastparent = parent
        node = [key,page.value['title'], count, {}]
        sitemap.append(node)
    sitemap.extend(get_workshop_nodes(C))
    sitemap.extend(get_news_nodes(C))
    sitemap.extend(get_events_nodes(C))
    return create_sitemap(sitemap)
