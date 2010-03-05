import logging
from restish import http, resource
import adminish

from examplesite.lib import guard


log = logging.getLogger(__name__)


class Root(resource.Resource):
    @resource.GET()
    def html(self, request):
        return http.ok([('Content-Type', 'text/html')],
            "<p>Hello from examplesite!</p>")

    @guard.guard(guard.is_admin()) 
    @resource.child() 
    def admin(self, request, segments): 
        return adminish.resource.Admin() 


