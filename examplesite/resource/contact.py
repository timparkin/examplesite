
import smtplib
import formish, schemaish
from validatish import validator
from restish import resource, http, templating

from examplesite.lib import base

from examplesite.resource import navigation



class ContactSchema(schemaish.Structure):
    """ A simple sommets form """
    email = schemaish.String(validator=validator.All(validator.Required(), validator.Email()))
    name = schemaish.String(validator=validator.Required())
    phone = schemaish.String(title="Phone Number")
    address = schemaish.String()
    comment = schemaish.String()
    optin = schemaish.Boolean(title='Subscribe', description='If you would like to receive information electronically, please tick the box')

def get_contact_form():
    """ Creates a form and assigns a widget """
    form = formish.Form(ContactSchema(),name="contact")
    form['address'].widget = formish.TextArea()
    form['comment'].widget = formish.TextArea()
    form['optin'].widget = formish.Checkbox()
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
           'subject': 'Contact for Joe Cornish',
           'args': {'data':data},
           'from': 'orders@joecornish.com',
           }
        send_email(request, email, 'Customer/Contact')
        return http.see_other('/contact-thanks')

