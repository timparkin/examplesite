from datetime import date

from menuish.menu import create_sitemap
from operator import itemgetter





def get_news_nodes(C):
    with C.session() as S:
        newsitems = S.docs_by_view('newsitem/all')
    newsitems = sorted(newsitems,key=itemgetter('date'), reverse=True)
    nodes = []
    for newsitem in newsitems:
        if newsitem['date'] < date.today():
            nodes.append( ['root.news.%s'%newsitem['_id'],newsitem['menu_title'], 1, {}] )
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
    sitemap.extend(get_news_nodes(C))
    return create_sitemap(sitemap)
