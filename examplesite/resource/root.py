from __future__ import with_statement
import logging
from restish import http, resource, templating
import adminish
from datetime import date

from wsgiapptools import flash
from formish.fileresource import FileResource
from formish.filestore import CachedTempFilestore, FileSystemHeaderedFilestore

from examplesite.resource import redirect, gallery, navigation, items, basket, checkout, contact
from examplesite.lib import base, guard

from examplesite.lib.filestore import CouchDBAttachmentSource




log = logging.getLogger(__name__)

def send_email(request, email, template_name):
    notification = request.environ['notification']
    headers = {"To": email['to'],
               "Subject": email['subject']}
    msg = notification.buildEmailFromTemplate(
            template_name, email['args'], headers)
    server = smtplib.SMTP(notification.smtpHost)
    server.sendmail(notification.emailFromAddress, [email['to']], str(msg))

class Root(redirect.Root):

    def dispatch(self, request, segments):
        url = '/'+'/'.join(segments)
        if len(segments) > 1:
            if segments[0] == 'about' and url.endswith('.asp'):
                return http.moved_permanently('/about')
            if segments[0] in ['portfolio','products'] and url.endswith('.asp'):
                return http.moved_permanently('/gallery')
            if len(segments) == 1 and segments[0] in ['portfolio','products']:
                return http.moved_permanently('/gallery')
            if segments[0] == 'events':
                return http.moved_permanently('/news')
            if segments[0] == 'news' and  url.endswith('.asp'):
                return http.moved_permanently('/news')
            if segments[0] == 'contact' and url.endswith('.asp'):
                return http.moved_permanently('/contact')
            if segments[0] == 'workshop':
                return http.moved_permanently('/workshops')

        return RootResource()


class RootResource(base.BasePage):

    @resource.GET()
    def html(self, request):
        C = request.environ['couchish']
        with C.session() as S:
            results = list(S.view('page/by_url',key='/',include_docs=True))
            news = S.docs_by_view('newsitem/homepage_news')
        news = [n for n in news if n.get('date') and n['date'] < date.today()]
        page = results[0].doc
        sitemap = navigation.get_navigation(request)
        data = {'page': page, 'request': request, 'sitemap': sitemap, 'news':news}
        out = templating.render(request, page['pagetype'], data, encoding='utf-8')
        return http.ok([('Content-Type', 'text/html')], out)

    @guard.guard(guard.is_admin())
    @resource.child()
    def admin(self, request, segments):
        return adminish.resource.Admin()

    @resource.child('admin/photo_csv')
    def photo_csv(self, request, segments):
        return PhotoCSVResource()

    @resource.child('admin/product_csv')
    def product_csv(self, request, segments):
        return ProductCSVResource()

    @resource.child('admin/user_csv')
    def user_csv(self, request, segments):
        return UserCSVResource()

    @resource.child()
    def basket(self, request, segments):
        return basket.BasketResource()

    @resource.child(resource.any)
    def page(self, request, segments):
        return PageResource(segments), ()

    @resource.child()
    def gallery(self, request, segments):
        return gallery.Gallery()

    @resource.child()
    def photos(self, request, segments):
        return gallery.Gallery('photo')

    @resource.child()
    def news(self, request, segments):
        return items.News()

    @resource.child()
    def workshops(self, request, segments):
        return items.Workshops()

    @resource.child()
    def checkout(self, request, segments):
        return checkout.CheckoutResource()

    @resource.child()
    def contact(self, request, segments):
        return contact.ContactResource()

    @resource.child('filehandler')
    def filehandler(self, request, segments):
        cdbfilestore = CouchDBAttachmentSource(request.environ['couchish'])
        cache = CachedTempFilestore(FileSystemHeaderedFilestore(root_dir='cache'))
        return FileResource(filestores=cdbfilestore,cache=cache)

    @resource.child()
    def _callback(self, request, segments):
        order_timestamp = request.GET.get('order_timestamp')
        transactionnumber = request.GET.get('transactionnumber')
        transactiontime = request.GET.get('transactiontime')
        failurereason = request.GET.get('failurereason')
        print '***transaction'
        print 'order_timestamp', order_timestamp
        print 'transactionnumber', transactionnumber
        print 'transactiontime',transactiontime
        print 'failurereason', failurereason

        username = request.GET.get('username')
        C = request.environ['couchish']
        with C.session() as S:
            customer = S.doc_by_view('user/by_identifiers', key=unicode(username))
        for attempted_order in customer.get('attempted_orders',[]):
            if attempted_order['order_timestamp'] == order_timestamp:
                break
        else:
            return

        if 'transactions' not in attempted_order:
            attempted_order['transactions'] = []

        if failurereason:
            transaction = {
                    'succeeded': False,
                    'transactiontime': transactiontime,
                    'transactionnumber': transactionnumber,
                    'message': failurereason,
            }
            attempted_order['transactions'].append(transaction)
        else:
            cv2avsresult = request.GET.get('cv2avsresult')
            transaction = {
                    'succeeded': True,
                    'transactiontime': transactiontime,
                    'transactionnumber': transactionnumber,
                    'cv2avsresult': cv2avsresult,
            }
            attempted_order['transactions'].append(transaction)
            email = {
               'to': customer['email'],
               'subject': 'Order Confirmation',
               'args': {'transaction': transaction,'attempted_order': attempted_order},
               'from': 'orders@joecornish.com',
               }
            send_email(request, email, 'Order/Confirmation')

        return http.ok([('Content-Type','text/html')],'success %s'%transaction)


class PageResource(base.BasePage):

    def __init__(self, segments):
        self.segments = segments

    @resource.GET(accept='html')
    def page(self, request):
        sitemap = navigation.get_navigation(request)
        url = '/%s'%('/'.join(self.segments))

        C = request.environ['couchish']
        with C.session() as S:
            results = list(S.view('page/by_url',key=url,include_docs=True))
        page = results[0].doc
        data = {'page': page,'request':request, 'sitemap':sitemap}
        return templating.render_response(request, self, page['pagetype'], data)


