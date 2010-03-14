from __future__ import with_statement
import cgi
from wsgiapptools import cookies
from couchish import errors

def authenticate(credentials, environ):
    """
    Authenticate the given credentials returning a username or None.
    """
    if 'password' in credentials:
        return _authenticate_password(credentials, 'password', environ)


def set_authenticated_username(request, username):
    """
    Automatically log in.
    """
    # Find the reqoze.who plugin that will remember the identity.
    rememberer = request.environ['repoze.who.plugins']['auth_tkt']
    # Build an identity. repoze.who seems to only *need* the username but there
    # are other bits that can go in the cookie.
    identity = {'repoze.who.userid': username}
    # Set the cookies that the remember says to set.
    cookie_mgr = cookies.get_cookies(request.environ)
    # XXX IIdentifier.remember() sometimes returns None (if there's no changes)
    # so we can't blindly iterate the returned value.
    headers = rememberer.remember(request.environ, identity)
    if headers:
        for _, cookie_header in headers:
            cookie_mgr.set_cookie(cookie_header)

def _authenticate_password(credentials, password, environ):
    """
    Authenticate password credentials.
    """
    try:
        C = environ['couchish']
        with C.session() as S:
            user = S.doc_by_view('user/by_identifiers', key=credentials['username'])
        if credentials['password'] != user['credentials']['password']:
            return None
    except errors.NotFound:
        return None
    return user['username']


def make_authenticator_plugin():
    return AuthenticatorPlugin()


class AuthenticatorPlugin(object):
    """
    reqpoze.who authenticator that tries to authenticate the identity as admin
    infomy login account.
    """

    def authenticate(self, environ, identity):
        # Basic sanity check.
        if 'repoze.who.plugins.auth_tkt.userid' in identity:
            return identity['repoze.who.plugins.auth_tkt.userid']
        if 'login' not in identity:
            return None
        # Extract the credentials from the identity.
        if 'password' in identity:
            credentials = {'username': identity['login'], 'password': identity['password']}
        else:
            return None
        # Try to authenticate the user.
        username = authenticate(credentials, environ)
        if username is None:
            return None
        return username

