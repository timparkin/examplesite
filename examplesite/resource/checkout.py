# encoding: utf-8
from __future__ import with_statement
from itertools import chain, repeat, izip

from restish import resource, http, templating
from wsgiapptools import cookies
from couchish import errors
from couchdb.client import ResourceNotFound

from commerce import basket as c_basket

from examplesite import who, auth
from examplesite.lib import basket
from examplesite.resource import login
from datetime import datetime

import formish, schemaish, validatish

import logging

log = logging.getLogger(__name__)

country_options = [
("1","United Kingdom"),
("7","United States"),
("9","Afghanistan"),
("10","Albania"),
("11","Algeria"),
("12","Andorra"),
("13","Argentina"),
("5","Australia"),
("14","Austria"),
("15","Belgium"),
("16","Brazil"),
("8","Canada"),
("17","China"),
("18","Croatia"),
("19","Cuba"),
("20","Cyprus"),
("21","Czech Republic"),
("22","Denmark"),
("23","Finland"),
("24","France"),
("25","Germany"),
("26","Greece"),
("27","Hong Kong"),
("29","Hungary"),
("28","Iceland"),
("30","Ireland"),
("31","Italy"),
("32","Japan"),
("33","Kenya"),
("34","Luxembourg"),
("35","Malta"),
("36","Netherlands"),
("37","New Zealand"),
("38","Norway"),
("39","Poland"),
("40","Portugal"),
("41","South Africa"),
("42","Spain"),
("43","Sweden"),
("44","Switzerland"),
("6","Thailand"),
("45","United Arab Emirates"),
        ]

def make_form(request, *args, **kwargs):
    kwargs['renderer'] = request.environ['restish.templating'].renderer
    return formish.Form(*args, **kwargs)

def checkout_form(request, **k):
    schema = schemaish.Structure()
    schema.add('billing_street1', schemaish.String(title="Street",validator=validatish.Required()))
    schema.add('billing_street2', schemaish.String(title=""))
    schema.add('billing_street3', schemaish.String(title=""))
    schema.add('billing_city', schemaish.String(title="City/Town",validator=validatish.Required()))
    schema.add('billing_county', schemaish.String(title="County"))
    schema.add('billing_postcode', schemaish.String(title="Postcode",validator=validatish.Required()))
    schema.add('billing_country', schemaish.String(title="Country",validator=validatish.Required()))
    schema.add('delivery_street1', schemaish.String(title="Street",validator=validatish.Required()))
    schema.add('delivery_street2', schemaish.String(title=""))
    schema.add('delivery_street3', schemaish.String(title=""))
    schema.add('delivery_city', schemaish.String(title="City/Town",validator=validatish.Required()))
    schema.add('delivery_county', schemaish.String(title="County"))
    schema.add('delivery_postcode', schemaish.String(title="Postcode",validator=validatish.Required()))
    schema.add('delivery_country', schemaish.String(title="Country",validator=validatish.Required()))
    schema.add('filename', schemaish.String())
    schema.add('secuitems', schemaish.String())
    schema.add('shreference', schemaish.String())
    schema.add('cardholdersname', schemaish.String())
    schema.add('deliveryname', schemaish.String())
    schema.add('cardholdersemail', schemaish.String(title="Email"))
    schema.add('cardholdersphonenumber', schemaish.String(title="Phone Number"))
    schema.add('transactioncurrency', schemaish.String())
    schema.add('products_price', schemaish.String())
    schema.add('shippingcharge', schemaish.String())
    schema.add('transactiontax', schemaish.String())
    schema.add('transactionamount', schemaish.String())
    return make_form(request, schema, **k)

def make_checkout_form(request):
    form = checkout_form(request, add_default_action=False)
    form.add_action('submit','Proceed to Credit Card Page')
    form['filename'].widget = formish.Hidden()
    form['secuitems'].widget = formish.Hidden()
    form['shreference'].widget = formish.Hidden()
    form['cardholdersname'].widget = formish.Hidden()
    form['deliveryname'].widget = formish.Hidden()
    form['transactioncurrency'].widget = formish.Hidden()
    form['products_price'].widget = formish.Hidden()
    form['shippingcharge'].widget = formish.Hidden()
    form['transactiontax'].widget = formish.Hidden()
    form['transactionamount'].widget = formish.Hidden()
    form['billing_country'].widget = formish.SelectChoice(options=country_options)
    form['delivery_country'].widget = formish.SelectChoice(options=country_options)

    return form




def registration_form(request,**k):
    schema = schemaish.Structure()
    schema.add('title', schemaish.String(validator=validatish.Required()))
    schema.add('first_names', schemaish.String(validator=validatish.Required()))
    schema.add('last_name', schemaish.String(validator=validatish.Required()))
    schema.add('email', schemaish.String(validator=validatish.Required()))
    schema.add('telephone', schemaish.String())
    schema.add('password', schemaish.String(validator=validatish.Required()))
    address = schemaish.Structure()
    address.add('street1', schemaish.String(validator=validatish.Required()))
    address.add('street2', schemaish.String())
    address.add('street3', schemaish.String())
    address.add('city', schemaish.String(validator=validatish.Required()))
    address.add('county', schemaish.String(validator=validatish.Required()))
    address.add('postcode', schemaish.String(validator=validatish.Required()))
    address.add('country', schemaish.String(validator=validatish.Required()))
    schema.add('address',address)
    return make_form(request, schema, **k)

def make_registration_form(request, **k):
    form = registration_form(request, **k)
    form['password'].widget = formish.CheckedPassword()
    form['address.country'].widget = formish.SelectChoice(options=country_options)
    return form

   
    


def autosubmit_form(request, **k):
    schema = schemaish.Structure()
    schema.add('billing_street1', schemaish.String(title="Street",validator=validatish.Required()))
    schema.add('billing_street2', schemaish.String(title=""))
    schema.add('billing_street3', schemaish.String(title=""))
    schema.add('billing_city', schemaish.String(title="City/Town",validator=validatish.Required()))
    schema.add('billing_county', schemaish.String(title="County"))
    schema.add('billing_postcode', schemaish.String(title="Postcode",validator=validatish.Required()))
    schema.add('billing_country', schemaish.String(title="Country",validator=validatish.Required()))
    schema.add('delivery_street1', schemaish.String(title="Street",validator=validatish.Required()))
    schema.add('delivery_street2', schemaish.String(title=""))
    schema.add('delivery_street3', schemaish.String(title=""))
    schema.add('delivery_city', schemaish.String(title="City/Town",validator=validatish.Required()))
    schema.add('delivery_county', schemaish.String(title="County"))
    schema.add('delivery_postcode', schemaish.String(title="Postcode",validator=validatish.Required()))
    schema.add('delivery_country', schemaish.String(title="Country",validator=validatish.Required()))
    schema.add('filename', schemaish.String())
    schema.add('secuitems', schemaish.String())
    schema.add('shreference', schemaish.String())
    schema.add('cardholdersname', schemaish.String())
    schema.add('deliveryname', schemaish.String())
    schema.add('cardholdersemail', schemaish.String(title="Email"))
    schema.add('cardholdersphonenumber', schemaish.String(title="Phone Number"))
    schema.add('transactioncurrency', schemaish.String())
    schema.add('products_price', schemaish.String())
    schema.add('shippingcharge', schemaish.String())
    schema.add('transactiontax', schemaish.String())
    schema.add('transactionamount', schemaish.String())
    schema.add('order_timestamp', schemaish.String())
    schema.add('checkcode', schemaish.String())
    schema.add('callbackurl', schemaish.String())
    schema.add('callbackdata', schemaish.String())
    return make_form(request, schema, **k)

def make_autosubmit_form(request):
    form = autosubmit_form(request, action_url="https://test.secure-server-hosting.com/secutran/secuitems.php", add_default_action=False, name="autosubmitform")
    form.add_action('autosubmit','if you are not redirected, please click here')
    form['filename'].widget = formish.Hidden()
    form['checkcode'].widget = formish.Hidden()
    form['secuitems'].widget = formish.Hidden()
    form['shreference'].widget = formish.Hidden()
    form['cardholdersname'].widget = formish.Hidden()
    form['deliveryname'].widget = formish.Hidden()
    form['transactioncurrency'].widget = formish.Hidden()
    form['products_price'].widget = formish.Hidden()
    form['shippingcharge'].widget = formish.Hidden()
    form['transactiontax'].widget = formish.Hidden()
    form['transactionamount'].widget = formish.Hidden()
    form['billing_street1'].widget = formish.Hidden()
    form['billing_street2'].widget = formish.Hidden()
    form['billing_street3'].widget = formish.Hidden()
    form['billing_city'].widget = formish.Hidden()
    form['billing_county'].widget = formish.Hidden()
    form['billing_postcode'].widget = formish.Hidden()
    form['billing_country'].widget = formish.Hidden()
    form['delivery_street1'].widget = formish.Hidden()
    form['delivery_street2'].widget = formish.Hidden()
    form['delivery_street3'].widget = formish.Hidden()
    form['delivery_city'].widget = formish.Hidden()
    form['delivery_county'].widget = formish.Hidden()
    form['delivery_postcode'].widget = formish.Hidden()
    form['delivery_country'].widget = formish.Hidden()
    form['cardholdersemail'].widget = formish.Hidden()
    form['cardholdersphonenumber'].widget = formish.Hidden()
    form['order_timestamp'].widget = formish.Hidden()
    form['callbackurl'].widget = formish.Hidden()
    form['callbackdata'].widget = formish.Hidden()
    return form

class LoginResource(resource.Resource):

    # This handles basic logging in - we need to include a link to 

    @resource.GET()
    def GET(self, request):
        identity = who.get_identity(request)
        if identity.has_permission('purchase'):
            return http.see_other('/checkout')
        return self.html(request)

    @templating.page('checkout/login.html')
    def html(self, request, registration_form=None):
        form = login.login_form(request, came_from=request.url)
        if registration_form == None:
            registration_form = make_registration_form(request)
        return {'form': form, 'request':request, 'registration_form':registration_form}



    @resource.POST()
    def POST(self, request):
        form = make_registration_form(request)
        try:
            data = form.validate(request)
        except formish.FormError:
            return self.html(request, form)
        C = request.environ['couchish']
        try:
            with C.session() as S:
                customer = S.doc_by_view('user/by_identifiers', key=data['email'])
            form.errors['email'] = 'already exists'
            return self.html(request, form)
        except errors.NotFound:
            pass

        customer = {
            'model_type': 'user',
            'ctime': datetime.now().isoformat(),
            'mtime': datetime.now().isoformat(),
            'title': data['title'],
            'first_names': data['first_names'],
            'last_name': data['last_name'],
            'email': data['email'],
            'username': data['email'],
            'telephone': data['telephone'],
            'credentials': {
                'password': data['password'].decode('utf8')
            },
            'address': {
                'street1': data['address']['street1'],
                'street2': data['address']['street2'],
                'street3': data['address']['street3'],
                'street4': '',
                'city': data['address']['city'],
                'county': data['address']['county'],
                'postcode': data['address']['postcode'],
                'country': data['address']['country'],
            },
           'roles': [ "_system/customer" ]
        }

        with C.session() as S:
            id = S.create(customer)
        auth.set_authenticated_username(request, data['email'])
        return http.see_other('/checkout')


class CheckoutResource(resource.Resource):

    @resource.GET()
    def GET(self, request):
        identity = who.get_identity(request)
        if not identity.has_permission('purchase'):
            return http.see_other('/checkout/login')

        # Store the basket on the persons user account
        return self.html(request)

    @resource.POST()
    def POST(self, request):
        identity = who.get_identity(request)
        if not identity.has_permission('purchase'):
            return http.see_other('/checkout/login')

        form = make_checkout_form(request)
        try:
            data = form.validate(request)
        except formish.FormError:
            return self.html(request, form)
        C = request.environ['couchish']
        with C.session() as S:
            customer = S.doc_by_view('user/by_identifiers', key=identity.email)
            customer['address'] = {
                'street1': data['billing_street1'],
                'street2': data['billing_street2'],
                'street3': data['billing_street3'],
                'city': data['billing_city'],
                'county': data['billing_county'],
                'postcode': data['billing_postcode'],
                'country': data['billing_country'],
                    }
        # send an auto submitting form... 
        return self.auto_submit_form(request, data)

        

    @templating.page('checkout/checkout.html')
    def html(self, request, form=None):
        b = basket.Basket(request)
        b.load()
        if form is None:
            secuitems = ''
            for item in b._items:
                secuitems += '[%s||%s|%0.2f|%s|%0.2f]'%(item.id, item.description, item.unit_price, item.quantity,item.unit_price*item.quantity)
            form = make_checkout_form(request)
            identity = who.get_identity(request)
            form.defaults = {
                'billing_street1': identity.address['street1'], 
                'billing_street2': identity.address['street2'], 
                'billing_street3': identity.address['street3'], 
                'billing_city': identity.address['city'], 
                'billing_county': identity.address['county'], 
                'billing_postcode': identity.address['postcode'], 
                'billing_country': identity.address['country'], 
                'delivery_street1': identity.address['street1'], 
                'delivery_street2': identity.address['street2'], 
                'delivery_street3': identity.address['street3'], 
                'delivery_city': identity.address['city'], 
                'delivery_county': identity.address['county'], 
                'delivery_postcode': identity.address['postcode'], 
                'delivery_country': identity.address['country'], 
                'filename': 'sh210209/template.html',
                'secuitems': secuitems,
                'shreference': 'sh210209',
                'cardholdersname': identity.full_name,
                'cardholdersemail': identity.email,
                'cardholdersphonenumber': identity.telephone,
                'deliveryname': identity.full_name,
                'transactioncurrency': 'GBP',
                'products_price': '%0.2f'%b.products_price,
                'shippingcharge': '%0.2f'%b.postage_price,
                'transactiontax': '%0.2f'%((b.total_price*0.175)/1.175),
                'transactionamount': '%0.2f'%b.total_price,
            }
        return {'form': form, 'request': request}

    @templating.page('/checkout/autosubmit.html')
    def auto_submit_form(self, request, data):
        identity = who.get_identity(request)
        C = request.environ['couchish']
        order_timestamp = datetime.now().isoformat()
        data['order_timestamp'] = order_timestamp
        data['checkcode'] = '108088'
        data['callbackurl'] = 'http://jc.timparkin.co.uk/_callback'
        data['callbackdata'] = 'username|%s|order_timestamp|%s'%(identity.username, order_timestamp)
        b = basket.Basket(request)
        b.load()
        # Clear basket
        form = make_autosubmit_form(request)
        form.defaults = data
        order_items = []
        for item in b._items:
            order_items.append( {'id': str(item.id), 'code': str(item.item.code), 'description': str(item.description), 'price': float(item.unit_price),'quantity': int(item.quantity), 'postage': float(item.unit_postage)} )
        with C.session() as S:
            customer = S.doc_by_view('user/by_identifiers', key=unicode(identity.username))
            if 'attempted_orders' not in customer:
                customer['attempted_orders'] = []
            customer['attempted_orders'].append( {
                    'order_timestamp': order_timestamp,
                    'items': order_items,
                    'postage': float(b.postage_price),
                    'total_price': float(b.total_price),
                    } )

        b.empty()
        return {'form': form}

    @resource.child()
    def login(self, request, segments):
        return LoginResource()

    @resource.child()
    def registration(self, request, segments):
        return RegistrationResource()

    @resource.child()
    def card(self, request, segments):
        return CardResource()

    @resource.child()
    def forgot(self, request, segments):
        return ForgotResource()

    @resource.child()
    def thanks(self, request, segments):
        return CheckoutThanksResource()


class CardResource(resource.Resource):

    @resource.GET()
    def get(self, request):
        identity = who.get_identity(request)
        if not identity.has_permission('purchase'):        
            return http.see_other('/basket/login')
        return self.html(request)
        
    @resource.POST()
    def POST(self, request):
        identity = who.get_identity(request)
        if not identity.has_permission('purchase'):
            return http.see_other('/basket/login')

        form = make_card_form(request)
        try:
            data = form.validate(request)
        except formish.FormError:
            return self.html(request, form)
        return self.html(request)

    @templating.page('checkout/card.html')
    def html(self, request, form=None):
        if form is None:
            form = make_card_form(request)
        return {'form': form, 'request':request}


class CheckoutThanksResource(resource.Resource):

    @resource.GET()
    def get(self, request):
        b = basket.Basket(request)
        b.load()
        b.empty()
        b.save()
        return self.html(request)

    @templating.page('checkout/thanks.html')
    def html(self, request):
        return {'request': request}
