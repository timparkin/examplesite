from examplesite.lib import base

class Root(base.BasePage):

    def resource_child(self, request, segments):
        return self.dispatch(request, segments)

    def __call__(self, request):
        return self.dispatch(request, [])

    def dispatch(self, request, segments):
        url = '/'+'/'.join(segments)
        #if len(segments) > 1:
        #    if segments[0] == 'index.html':
        #        return http.moved_permanently('/')

        return RootResource()

