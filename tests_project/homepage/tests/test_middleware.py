from django.test import TestCase


class Tester(TestCase):

    # /app/page.function/urlparams
    def test_app_page_function(self):
        resp = self.client.get('/homepage/index.basic/1/2/3/')
        self.assertEqual(resp.status_code, 200)
        req = resp.wsgi_request
        self.assertEqual(req.dmp.app, 'homepage')
        self.assertEqual(req.dmp.page, 'index')
        self.assertEqual(req.dmp.function, 'basic')
        self.assertEqual(req.dmp.module, 'homepage.views.index')
        self.assertEqual(req.dmp.urlparams, [ '1', '2', '3' ])
        from homepage.views import index
        self.assertEqual(req.dmp.view_type, 'function')
        self.assertEqual(req.dmp.callable, index.basic)

    # /app/page/urlparams
    def test_app_page(self):
        resp = self.client.get('/homepage/index/1/2/3/')
        self.assertEqual(resp.status_code, 200)
        req = resp.wsgi_request
        self.assertEqual(req.dmp.app, 'homepage')
        self.assertEqual(req.dmp.page, 'index')
        self.assertEqual(req.dmp.function, 'process_request')
        self.assertEqual(req.dmp.module, 'homepage.views.index')
        self.assertEqual(req.dmp.urlparams, [ '1', '2', '3' ])
        from homepage.views import index
        self.assertEqual(req.dmp.view_type, 'function')
        self.assertEqual(req.dmp.callable, index.process_request)

    # /app
    def test_app(self):
        resp = self.client.get('/index/')
        self.assertEqual(resp.status_code, 200)
        req = resp.wsgi_request
        self.assertEqual(req.dmp.app, 'homepage')
        self.assertEqual(req.dmp.page, 'index')
        self.assertEqual(req.dmp.function, 'process_request')
        self.assertEqual(req.dmp.module, 'homepage.views.index')
        self.assertEqual(req.dmp.urlparams, [])
        from homepage.views import index
        self.assertEqual(req.dmp.view_type, 'function')
        self.assertEqual(req.dmp.callable, index.process_request)

    # /page.function/urlparams
    def test_page_function(self):
        resp = self.client.get('/index.basic/1/2/3/')
        self.assertEqual(resp.status_code, 200)
        req = resp.wsgi_request
        self.assertEqual(req.dmp.app, 'homepage')
        self.assertEqual(req.dmp.page, 'index')
        self.assertEqual(req.dmp.function, 'basic')
        self.assertEqual(req.dmp.module, 'homepage.views.index')
        self.assertEqual(req.dmp.urlparams, [ '1', '2', '3' ])
        from homepage.views import index
        self.assertEqual(req.dmp.view_type, 'function')
        self.assertEqual(req.dmp.callable, index.basic)

    # /page/urlparams
    def test_page(self):
        resp = self.client.get('/index/1/2/3/')
        self.assertEqual(resp.status_code, 200)
        req = resp.wsgi_request
        self.assertEqual(req.dmp.app, 'homepage')
        self.assertEqual(req.dmp.page, 'index')
        self.assertEqual(req.dmp.function, 'process_request')
        self.assertEqual(req.dmp.module, 'homepage.views.index')
        self.assertEqual(req.dmp.urlparams, [ '1', '2', '3' ])
        from homepage.views import index
        self.assertEqual(req.dmp.view_type, 'function')
        self.assertEqual(req.dmp.callable, index.process_request)

    # / with nothing else
    def test_nothing_else(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        req = resp.wsgi_request
        self.assertEqual(req.dmp.app, 'homepage')
        self.assertEqual(req.dmp.page, 'index')
        self.assertEqual(req.dmp.function, 'process_request')
        self.assertEqual(req.dmp.module, 'homepage.views.index')
        self.assertEqual(req.dmp.urlparams, [])
        from homepage.views import index
        self.assertEqual(req.dmp.view_type, 'function')
        self.assertEqual(req.dmp.callable, index.process_request)
