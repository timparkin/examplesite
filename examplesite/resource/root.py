from __future__ import with_statement
import logging
from restish import http, resource, templating
import adminish
from datetime import date

from wsgiapptools import flash
import formish, schemaish
from validatish import validator
from formish.fileresource import FileResource
from formish.filestore import CachedTempFilestore, FileSystemHeaderedFilestore

from examplesite.resource import redirect, navigation, items, contact
from examplesite.lib import base, guard

from examplesite.lib.filestore import CouchDBAttachmentSource

log = logging.getLogger(__name__)

class ContactSchema(schemaish.Structure):
    """ A simple sommets form """
    email = schemaish.String(validator=validator.All(validator.Required(), validator.Email()))
    name = schemaish.String(validator=validator.Required())
    message = schemaish.String()

def get_contact_form():
    """ Creates a form and assigns a widget """
    form = formish.Form(ContactSchema(),action_url='/contact',name="contact",add_default_action=False)
    form.add_action(name='submit', value='Click Here to Send')
    form['message'].widget = formish.TextArea()
    return form

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
        form = get_contact_form()
        socialmedia = C.db['socialmedia']
        data = {'page': page, 'request': request, 'sitemap': sitemap,
                'news':news, 'form': form, 'blog': socialmedia['blog'],
                'twitter': socialmedia['twitter']}
        out = templating.render(request, '/page-templates/%s'%page['template'], data, encoding='utf-8')
        return http.ok([('Content-Type', 'text/html')], out)

    @guard.guard(guard.is_admin())
    @resource.child()
    def admin(self, request, segments):
        return adminish.resource.Admin()

    @resource.child(resource.any)
    def page(self, request, segments):
        return PageResource(segments), ()

    @resource.child()
    def news(self, request, segments):
        return items.News()

    @resource.child()
    def contact(self, request, segments):
        return contact.ContactResource()

    @resource.child('filehandler')
    def filehandler(self, request, segments):
        cdbfilestore = CouchDBAttachmentSource(request.environ['couchish'])
        cache = CachedTempFilestore(FileSystemHeaderedFilestore(root_dir='cache'))
        return FileResource(filestores=cdbfilestore,cache=cache)


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
        form = get_contact_form()
        data = {'page': page,'request':request, 'sitemap':sitemap, 'form':
                form}
        return templating.render_response(request, self, '/page-templates/%s'%page['template'], data)


