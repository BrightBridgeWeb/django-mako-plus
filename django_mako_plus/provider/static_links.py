from django.conf import settings
from django.utils.module_loading import import_string

from ..util import merge_dicts, flatten, log, crc32
from ..version import __version__
from .base import BaseProvider

import logging
import os
import os.path
import json
import glob
from collections import namedtuple


#####################################################
###   Abstract Link Provider

class LinkProvider(BaseProvider):
    '''
    Renders links like <link> and <script> based on the name of the template
    and supertemplates.
    '''
    # the default options are for CSS files
    default_options = merge_dicts(BaseProvider.default_options, {
        # subclasses should override the group
        'group': 'scripts',
        # string for the absolute path to the filename that should be linked (if it exists)
        # if this is a function/lambda, DMP will run the function to get the string path
        'filename': 'app/subdir/template.ext',
        # whether to skip duplicate urls generated in the same provider run
        'skip_duplicates': False,
    })
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        filepath = self.options['filename']
        if callable(filepath):  # if a function, call it to get the path
            filepath = filepath(self)
        self.filename = os.path.relpath(filepath, settings.BASE_DIR).replace('\\', '/')
        if log.isEnabledFor(logging.DEBUG):
            log.debug('[%s] %s searching for %s', self.template_file, self.__class__.__qualname__, self.filename)
        try:
            self.mtime = int(os.stat(filepath).st_mtime)
            if log.isEnabledFor(logging.INFO):
                log.info('[%s] found %s', self.template_file, self.filename)
            # version_id combines current time and the CRC32 checksum of file bytes
            self.version_id = (self.mtime << 32) | crc32(filepath)
        except FileNotFoundError:
            self.mtime = 0
            self.version_id = 0

    def start(self, provider_run, data):
        # (spans the entire list of providers during the run)
        provider_run.urls = set()
        # (spans only this provider across the template chain)
        data['urls'] = []

    def provide(self, provider_run, data):
        # delaying printing of tag because the JsContextProvider delays and this must go after it
        if self.mtime == 0:
            return
        url = '{}?v={:x}'.format(
            self.filename.replace('\\', '/'),
            self.version_id,
        )
        if not self.options['skip_duplicates'] or url not in provider_run.urls:
            provider_run.urls.add(url)
            data['urls'].append(url)

    def finish(self, provider_run, data):
        for url in data['urls']:
            provider_run.write(self.create_link(provider_run, url))

    def create_link(self, provider_run, url):
        raise NotImplementedError('Subclass did not implement `create_link()`')


#############################################
###   Css and Js Link Providers


class CssLinkProvider(LinkProvider):
    '''Generates a CSS <link>'''
    default_options = merge_dicts(LinkProvider.default_options, {
        'group': 'styles',
        'filename': lambda pr: os.path.join(*flatten(pr.app_config.path, 'styles', pr.subdir_parts[1:], pr.template_name + '.css')),
        'skip_duplicates': True,
    })

    def create_link(self, provider_run, url):
        '''Creates a link to the given URL'''
        return '<link data-context="{contextid}" rel="stylesheet" type="text/css" href="{static}{url}" />'.format(
            contextid=provider_run.uid,
            static=settings.STATIC_URL,
            url=url,
        )


class JsLinkProvider(LinkProvider):
    '''Generates a JS <script>.'''
    default_options = merge_dicts(LinkProvider.default_options, {
        'group': 'scripts',
        'filename': lambda pr: os.path.join(*flatten(pr.app_config.path, 'scripts', pr.subdir_parts[1:], pr.template_name + '.js')),
        'async': False,
        'skip_duplicates': False,
    })

    def create_link(self, provider_run, url):
        '''Creates a link to the given URL'''
        return '<script data-context="{contextid}" src="{static}{url}"{async}></script>'.format(
            contextid=provider_run.uid,
            static=settings.STATIC_URL,
            url=url,
            async=' async="async"' if self.options['async'] else '',
        )



###################################
###  JS Context Provider

class JsContextProvider(BaseProvider):
    '''
    Adds all js_context() variables to DMP_CONTEXT.
    This should be listed before JsLinkProvider so the
    context variables are available during <script> runs.
    '''
    default_options = merge_dicts(LinkProvider.default_options, {
        'group': 'scripts',
        'encoder': 'django.core.serializers.json.DjangoJSONEncoder',
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.encoder = import_string(self.options['encoder'])
        self.template = "{}/{}".format(self.app_config.name, self.template_name)

    def start(self, provider_run, data):
        data['templates'] = []

    def provide(self, provider_run, data):
        data['templates'].append(self.template)

    def finish(self, provider_run, data):
        if len(data['templates']) == 0:
            return
        context_data = {
            jscontext('__router__'): {
                'template': self.template,
                'app': provider_run.request.dmp.app if provider_run.request is not None else None,
                'page': provider_run.request.dmp.page if provider_run.request is not None else None,
            },
        }
        for k in provider_run.context.kwargs:
            if isinstance(k, jscontext):
                value = provider_run.context[k]
                context_data[k] = value.__jscontext__() if hasattr(value, '__jscontext__') else value
        provider_run.write('<script>')
        provider_run.write('DMP_CONTEXT.set("{version}", "{contextid}", {data}, {templates});'.format(
            version=__version__,
            contextid=provider_run.uid,
            data=json.dumps(context_data, cls=self.encoder, separators=(',', ':')) if context_data else '{}',
            templates=json.dumps(data['templates']),
        ))
        provider_run.write('</script>')


class jscontext(str):
    '''
    Marks a key in the context dictionary as a JS context item.
    JS context items are sent to the template like normal,
    but they are also added to the runtime JS namespace.

    See the tutorial for more information on this function.
    '''
    # no code needed, just using the class for identity
