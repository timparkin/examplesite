"""
Module of static system/application roles and functions to build
organisation-specific role names.

Roles are namespaced to avoid clashes between system/application roles and
organisation-specific roles.

The '_' prefix is reserved for internal use. An organisation name must
therefore never be allowed to start with an '_'.

_system namespace is used for system admin style roles, e.g.

    _system/administrator

<org> namespace is per-org/company, e.g.

     profiled/super-user
     profiled/administrator
     profiled/list-supervisor
     google/super-user
     google/administrator
     google/list-supervisor

_app namespace may be useful for "tagging" roles, although it doesn't quite feel right.

     _app/trusted
     _app/paying
"""

import itertools
from ConfigParser import ConfigParser

from examplesite import enum


class RBAC(object):
    """
    Role-based access control manager.
    
    Realistically RBAC manage the role patterns (system vs org) and the mapping
    from a concrete set of roles to a set of permissions.
    """

    def __init__(self, filename):
        self._filename = filename
        self._config = self._load_config()

    def permissions_for_roles(self, roles):
        """
        Return a set of permission names for the given list of roles.
        """
        permissions = set()
        for role_name in roles:
            # Map the system prefix to the '*' permission prefix.
            prefix, _ = split_role(role_name)
            if prefix == SYSTEM_PREFIX:
                prefix = '*'
            # Find the role's configuration.
            role_config = self._role_config(role_name)
            # Add the prefixed permissions to the full permissions set.
            for permission in role_config['permissions'].split():
                permissions.update(join_permission(prefix,p) for p in self.expand_permission(permission))
        # Return the set of permissions.
        return permissions

    def expand_permission(self, permission):
        """
        Expand the given permission into the full set of permissions.
        """
        def gen(permission):
            it = iter([permission])
            while True:
                permission = it.next()
                yield permission
                includes = self._permission_config(permission).get('includes')
                if includes:
                    it = itertools.chain(it, includes.split())
        return set(gen(permission))

    def role_label(self, role):
        """
        Construct a human label for the given role.
        """
        prefix, _ = split_role(role)
        label = self._role_config(role)['label']
        if prefix == SYSTEM_PREFIX:
            return label
        return label % (prefix,)

    def organisation_roles(self, domain_name):
        """
        Return a list of roles for the given organisation.
        """
        sections = (section.split(':', 1) for section in self._config.sections())
        roles = (section[1] for section in sections if section[0] == 'role')
        roles = (split_role(role) for role in roles)
        roles = (role[1] for role in roles if role[0] == '?')
        return (join_role(domain_name, role) for role in roles)

    def system_roles(self):
        """
        Return a list of roles for the given organisation.
        """
        sections = (section.split(':', 1) for section in self._config.sections())
        roles = (section[1] for section in sections if section[0] == 'role')
        roles = (split_role(role) for role in roles)
        roles = (role for role in roles if role[0] == '_system')
        return (join_role(prefix, role) for (prefix, role) in roles)

    def all_roles(self, domain_names):
        roles = []
        roles.extend(self.system_roles())
        for domain_name in domain_names:
            roles.extend(self.organisation_roles(domain_name))
        return roles

    def _load_config(self):
        config = ConfigParser()
        config.read(self._filename)
        return config

    def _role_config(self, role):
        """
        Find the configuration for the given role.
        """
        # Map an org-specific role to the generic org role.
        prefix, postfix = split_role(role)
        if prefix != SYSTEM_PREFIX:
            role = join_role('?', postfix)
        # Return the role from the config.
        return dict(self._config.items('role:%s'%(role,)))

    def _permission_config(self, permission):
        """
        Find the configuration for the given permission.
        """
        return dict(self._config.items('permission:%s'%(permission,)))


# For now, we just need a single RBAC instance and we can expose its methods at
# module scope.
_rbac = RBAC('roles.ini')
permissions_for_roles = _rbac.permissions_for_roles
role_label = _rbac.role_label
organisation_roles = _rbac.organisation_roles
organisation_roles = _rbac.organisation_roles
system_roles = _rbac.system_roles
all_roles = _rbac.all_roles
expand_permission = _rbac.expand_permission


def join_permission(namespace, permission):
    return "%s/%s" % (namespace, permission)


def join_role(namespace, role):
    """
    Build a fully-qualified role name from the given namespace and role.
    """
    return '%s/%s' % (namespace, role)


def split_role(role):
    """
    Split a fully-qualified role into a namepace and role.
    """
    return tuple(role.split('/', 1))


def organisation_role(organisation, role):
    """
    Return a role from the organisation and role parts.
    """
    return join_role(organisation, role)


# Role definitions. These need prefixing before they can be used.
System = enum.Enum(
        ('ADMINISTRATOR', 'administrator'))


# System roles. We can define these as constants because we know the prefix.
SYSTEM_PREFIX = '_system'
SYSTEM_ADMINISTRATOR = join_role(SYSTEM_PREFIX, System.ADMINISTRATOR)

