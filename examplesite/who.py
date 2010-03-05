from __future__ import with_statement
from examplesite import roles
from couchish import errors



class Identity(object):

    def __init__(self, user):
        self.username = user['username']
        self.tracking_uuid = user.get('tracking_uuid')
        self.roles = user.get('roles') or []
        self.permissions = roles.permissions_for_roles(self.roles)
        self.preferences = user.get('preferences') or {}
        first_names = user.get('first_names')
        last_name = user.get('last_name')
        self.address = user.get('address')
        self.email = user.get('email')
        self.telephone = user.get('telephone')
        if first_names and last_name:
            self.full_name = " ".join([first_names, last_name])
        else:
            self.full_name = None


    def has_permission(self, permission):
        """
        Check that the identity includes the given permission.
        """
        print 'self.permissions',self.permissions
        print 'checking for permission',permission
        print 'has_permissions',roles.join_permission('*', permission)
        return roles.join_permission('*', permission) in self.permissions

    def has_any_permission(self, permission):
        """
        Check if the identity includes any permission below the given named
        permission.
        """
        permissions = set(roles.join_permission('*', p) for p in roles.expand_permission(permission))
        return bool(permissions & self.permissions)

    def is_admin(self):
        return True


class AnonymousIdentity(object):
    """
    An "anonymous" identity, used when no one has signed in.

    The purpose of AnonymousIdentity is to provide sane defaults for anonymous
    users, especially including preferences and permissions.

    In general, application code should not care that the identity is for a
    signed in user or an anonymous user.

    However, certain attributes don't make any sense for an anonymouse user,
    e.g. anything related to the username, membership number, etc. We never
    want "None" to be displayed by accident so you must still test the identity
    (if identity: ...) in these cases.
    """

    def __init__(self):
        self.preferences = {}
        self.permissions = []
        self.roles = []

    def __nonzero__(self):
        return False

    def has_permission(self, permission):
        return False

    def has_any_permission(self, permission):
        return False

    def is_admin(self):
        return False


def get_identity(request_or_environ):
    """
    Return the identity object or None.
    """
    if isinstance(request_or_environ, dict):
        environ = request_or_environ
    else:
        environ = request_or_environ.environ
    who_identity = environ.get('repoze.who.identity')
    if who_identity is None:
        return AnonymousIdentity()
    return who_identity.get('examplesite')


def make_metadata_plugin(*a, **k):
    return MetadataPlugin()


class MetadataPlugin(object):
    """
    repoze.who metadata plugin that populates the identity with basic
    information about the authenticated user.
    """

    def add_metadata(self, environ, identity):
        # Lookup the user information.
        userid = identity.get('repoze.who.userid')
        try:
            # GET THE USER USING USERID
            C = environ['couchish']
            with C.session() as S:
                user = S.doc_by_view('user/by_identifiers',key=userid)
            identity['examplesite'] = Identity(user)
        except errors.NotFound:
            raise Exception("Looks like the current user's been removed from the database. Clean out your cookies and try again.")

