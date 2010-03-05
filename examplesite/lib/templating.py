"""
Templating support library and renderer configuration.
"""

from examplesite import who

from restish import templating


def make_templating(app_conf):
    """
    Create a Templating instance for the application to use when generating
    content from templates.
    """
    renderer = make_renderer(app_conf)
    return Templating(renderer)


class Templating(templating.Templating):
    """
    Application-specific templating implementation.

    Overriding "args" methods makes it trivial to push extra, application-wide
    data to the templates without any assistance from the resource.
    """

    def args(self, request):
        # Call the super class to get the basic set of args.
        args = super(Templating, self).args(request)
        # Push to the args and return them.
        args['identity'] = who.get_identity(request)
        return args

def make_renderer(app_conf):
    """
    Create and return a restish.templating "renderer".
    """

    import pkg_resources
    import os.path
    from restish.contrib.makorenderer import MakoRenderer
    return MakoRenderer(
            directories=[
                pkg_resources.resource_filename('examplesite', 'templates'),
                pkg_resources.resource_filename('formish', 'templates/mako'),
                pkg_resources.resource_filename('adminish', 'templates'),
                pkg_resources.resource_filename('pagingish', 'templates/mako'),
                ],
            module_directory=os.path.join(app_conf['cache_dir'], 'template'),
            input_encoding='utf-8', output_encoding='utf-8',
            default_filters=['unicode', 'h']
            )
