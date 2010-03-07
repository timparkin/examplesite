from __future__ import with_statement
from itertools import chain, repeat, izip

from restish import resource, http, templating
from wsgiapptools import cookies
from couchish import errors

from commerce import basket as c_basket

from examplesite import who
from examplesite.lib import basket
from examplesite.resource import checkout

import formish, schemaish, validatish

import logging

log = logging.getLogger(__name__)


    


class BasketResource(resource.Resource):

    @resource.GET()
    @templating.page('/basket/basket.html')
    def GET(self, request):
        b = basket.Basket(request)
        b.load()
        return {'b':b, 'request':request}

    @resource.POST()
    def POST(self, request):
        args = request.POST
        command = args.pop('command')
        func = getattr(self, 'command_%s'%command)
        basket = func(request, args)
        return http.see_other('/basket')

    def command_add(self, request, args):
        item_id = args['_id']
        quantity = int(args.get('_quantity', 1))
        option_id = args['_option']
        b = basket.Basket(request)
        b.load()
        C = request.environ['couchish']
        with C.session() as S:
            item = S.doc_by_id(item_id)
            item = item.__subject__
        b.add(basket.BasketItem(item),option_id,quantity)
        b.save()

    def command_update(self, request, args):
        b = basket.Basket(request)
        b.load()
        def parse(args):
            removals = []
            updates = []
            for id in args.getall('remove'):
                removals.append(id)
            for name, quantity in args.items():
                if not name.startswith('item_'):
                    continue
                id = name[5:]
                try:
                    quantity = int(quantity)
                except ValueError:
                    continue
                if id not in removals:
                    updates.append((id, quantity))
            return removals, updates
        # Parse the request
        removals, updates = parse(args)
        # Process removals.
        for removal in removals:
            b.remove(removal)
        # Process updates.
        for id, quantity in updates:
            b.update_quantity(id, quantity)
        b.save()
        


class LoginResource(resource.Resource):

    # This handles basic logging in - we need to include a link to 

    @resource.GET()
    @templating.page('checkout/login.html')
    def GET(self, request):
        identity = who.get_identity(request)
        if identity.has_permission('purchase'):
            return http.see_other('/basket/checkout')
        form = login.login_form(request, came_from=request.url)
        return {'form': form, 'request':request}


