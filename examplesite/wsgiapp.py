"""
WSGI/PasteDeploy application bootstrap module.
"""
import pkg_resources

from restish.app import RestishApp
import repoze.who.config
from wsgiapptools import cookies, flash
import adminish, couchish, couchdb
from adminish import index
from notification.mako.service import NotificationService

from examplesite.resource import root
from examplesite import hooks


def make_app(global_conf, **app_conf):
    """
    PasteDeploy WSGI application factory.

    Called by PasteDeply (or a compatable WSGI application host) to create the
    examplesite WSGI application.
    """
    app = RestishApp(root.Root())
    app = repoze.who.config.make_middleware_with_config(app, global_conf, app_conf['repoze.who.ini'])
    app = setup_environ(app, global_conf, app_conf)
    # General "middleware".
    app = flash.flash_middleware_factory(app)
    app = cookies.cookies_middleware_factory(app)
    return app


def wrap_hook(environ, hook):
    def _hook(additions, deletions, changes):
        hook(environ, additions, deletions, changes)
    return _hook

def setup_environ(app, global_conf, app_conf):
    """
    WSGI application wrapper factory for extending the WSGI environ with
    application-specific keys.
    """

    from examplesite.lib.templating import make_templating
    couchish_config = adminish.config.make_couchish_config(app_conf, 'examplesite.model')
    adminish_config = adminish.config.make_adminish_config(couchish_config, store_factory=lambda request: request.environ['couchish'])
    notification_service = NotificationService(global_conf['smtpHost'], emailFromAddress=global_conf['emailFromAddress'], swallowSMTPErrors=True, emailTemplateDir=global_conf['emailTemplateDir'])
    templating = make_templating(app_conf)

    def application(environ, start_response):

        # Add additional keys to the environ here.
        _db = couchdb.Database(app_conf['couchish.db.url'])
        cache_db = couchdb.Database(app_conf['cache.db.url'])
        db = couchish.CouchishStore(_db, couchish_config, pre_flush_hook=wrap_hook(environ, hooks.pre_flush_hook), post_flush_hook=wrap_hook(environ, hooks.post_flush_hook))
        environ['restish.templating'] = templating
        environ['couchish'] = db
        environ['cache'] = cache_db
        environ['adminish'] = adminish_config
        environ['searcher'] = index.Searcher(db, app_conf['index_dir'], adminish_config = adminish_config)
        environ['notification'] = notification_service
        return app(environ, start_response)

    return application

