# Copyright (c) 2010 Infrae / Technical University Delft. All rights reserved.
# See also LICENSE.txt

import urllib

from lxml import etree

NSMAP = {'wadl': 'http://research.sun.com/wadl/2006/10'}

class WADLMethod(object):
    def __init__(self, id, name, api):
        self.id = id
        self.api = api
        self.name = name
        self.url = u'/'.join(self.api.doc.xpath(
            '//wadl:method[@id="%s"]//ancestor::wadl:resource/@path' % self.id,
            namespaces=NSMAP))
        self.url = self.url.replace('//', '/').replace(
            '%', '%%').replace('{', '%(').replace('}', ')s')

        # XXX hack to fix broken fedora wadl.
        if not self.url.startswith('/objects'):
            self.url = '/objects%s' % self.url
        
    def __call__(self, **params):
        url = self.url % params
        return WADLRequest(url, self)

class WADLRequest(object):
    def __init__(self, url, method):
        self.url = url
        self.method = method
        self.headers = self.method.api.connection.form_headers.copy()

        self.param_types = {}
        self.undocumented_params = {} # needed in searchOjbects
        self.default_values = {}
        
        for param in self.method.api.doc.xpath(
            '//wadl:method[@id="%s"]/wadl:request/wadl:param' % self.method.id,
            namespaces=NSMAP):
            name = param.attrib['name']
            param_type = {'xs:int': int,
                          'xs:boolean': bool,
                          'xs:string': unicode}[param.attrib['type']]
            self.param_types[name] = param_type
            default_value = param.attrib.get('default')
            if default_value:
                self.default_values[name] = default_value
        

    def submit(self, body='', **params):
        qs = self.default_values.copy()
        for param, value in params.items():
            param_type = self.param_types.get(param)
            if param_type is None:
                raise KeyError('Method "%s" has no param "%s"' % (
                    self.method.id, param))
            if not isinstance(value, param_type):
                raise TypeError(
             'Expected %s for param "%s" on method "%s", got %s instead' % (
                    param_type,
                    param,
                    self.method.id,
                    value.__class__))
            
            if param_type is bool:
                value = unicode(param_type).lower()
            value = unicode(value)
            qs[param] = value
        for param, value in self.undocumented_params.items():
            if not param in qs:
                qs[param] = value
        if qs:
            self.url = '%s?%s' % (self.url, urllib.urlencode(qs))

        return self.method.api.connection.open(self.url,
                                               body,
                                               self.headers,
                                               method=self.method.name)
    
class API(object):
    def __init__(self, connection):
        self.connection = connection
        fp = self.connection.open('/objects/application.wadl')
        wadl_xml = fp.read()
        fp.close()
        self.doc = etree.fromstring(wadl_xml)
        for method in self.doc.xpath('//wadl:method',
                                     namespaces=NSMAP):
            method_id = method.attrib['id']
            method_name = method.attrib['name']
            self.__dict__[method_id] = WADLMethod(method_id, method_name, self)
        
