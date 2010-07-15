
import smtplib
import formish, schemaish
from validatish import validator
from restish import resource, templating

from examplesite.lib import base

from examplesite.resource import navigation



class ContactSchema(schemaish.Structure):
    """ A simple sommets form """
    email = schemaish.String(validator=validator.All(validator.Required(), validator.Email()))
    name = schemaish.String(validator=validator.Required())
    message = schemaish.String()


def get_contact_form():
    """ Creates a form and assigns a widget """
    form = formish.Form(ContactSchema(),name="contact",add_default_action=False)
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

class ContactResource(base.BasePage):

    @resource.GET()
    def GET(self, request):
        return self.html(request)

    @templating.page('page-contact.html')
    def html(self, request, form=None):
        C = request.environ['couchish']
        with C.session() as S:
            page = S.doc_by_view('page/by_url',key='/contact')
        sitemap = navigation.get_navigation(request)
        if form is None:
            form = get_contact_form()
        return {'request': request, 'sitemap': sitemap, 'page': page, 'form': form}

    @resource.POST()
    def POST(self, request):
        form = get_contact_form()
        try:
            data = form.validate(request)
        except formish.FormError:
            return self.html(request, form=form)
        email = {
           'to': 'tim.parkin@gmail.com',
           'subject': 'Contact from Optimum Exposure (%s)'%data['name'],
           'args': {'data':data},
           'from': data['email'],
           }
        send_email(request, email, 'Customer/Contact')
        return http.see_other('/contact-thanks')

