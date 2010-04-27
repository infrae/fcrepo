# Copyright (c) 2010 Infrae / Technical University Delft. All rights reserved.
# See also LICENSE.txt


from collections import defaultdict

from lxml import etree
from lxml.builder import ElementMaker

 
NAMESPACES = {'rdf': u'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
              'rdfs': u'http://www.w3.org/2000/01/rdf-schema#',
              'owl': u'http://www.w3.org/2002/07/owl#',
              'xsd': u'http://www.w3.org/2001/XMLSchema#',
              'fedora': u"info:fedora/fedora-system:def/relations-external#",
              'dc': u"http://purl.org/dc/elements/1.1/",
              'oai_dc': u"http://www.openarchives.org/OAI/2.0/oai_dc/",
              'dcterms': u'http://purl.org/dc/terms/'}

class Namespaces(dict):

    def __getattr__(self, prefix):
        value = self.get(prefix)
        if value is None:
            raise AttributeError('No such namespace prefix: %s' % prefix)

        ns = Namespace(value)
        return ns

    def url_split(self, url):
        name = url.rsplit('/', 1)[-1].rsplit(':', 1)[-1].rsplit('#', 1)[-1]
        ns = url[:-len(name)]
        return ns, name
        
    def prefix_url(self, url):
        ns, name = self.url_split(url)
        prefix = [prefix for (prefix, n) in self.items() if n == ns]
        if not prefix:
            raise ValueError('Can not prefix URL: "%s"' % url)
        return '%s:%s' % (prefix[0], name)

    def expand_url(self, url):
        prefix, rest = url.split(':', 1)
        try:
            ns = self[prefix]
        except KeyError:
            raise ValueError('Can not expand URL: "%s"' % url)
        return ns + rest

class Namespace(unicode):

    @property
    def title(self):
        return '%stitle' % self

    @property
    def format(self):
        return '%sformat' % self
    
    def __getattr__(self, name):
        return '%s%s' % (self, name)

    def __getitem__(self, name):
        return self.__getattr__(name)

NS = Namespaces(NAMESPACES)
NSXML = 'http://www.w3.org/XML/1998/namespace'

def dict2rdfxml(subject, predicates):
    rdf = ElementMaker(namespace=NS.rdf, nsmap=dict(NS))
    doc = rdf.RDF()
    subject = u'info:fedora/%s' % subject
    description= rdf.Description()
    description.attrib['{%s}about' % NS.rdf] = subject
    doc.append(description)
    
    for predicate, objects in predicates.items():
        ns, tagname = NS.url_split(predicate)
        for object in objects:
            el = etree.SubElement(description, '{%s}%s' % (ns, tagname))
            if object['type'] == 'uri':
                el.attrib['{%s}resource' % NS.rdf] = object['value']
            elif object['type'] == 'bnode':
                raise ValueError('Bnodes are not supported in Fedora')
            else:
                el.text = object['value']
                if object.get('lang'):
                    el.attrib['{%s}lang' % NSXML] = object['lang']
                elif object.get('datatype'):
                    el.attrib['{%s}datatype' % NS.rdf] = object['datatype']
                    
    return etree.tostring(doc,
                          encoding='UTF-8',
                          pretty_print=True,
                          xml_declaration=False)

def rdfxml2dict(rdfxml):
    doc = etree.fromstring(rdfxml)
    subject = None
    result = defaultdict(list)
    for description in doc:
        about = description.attrib['{%s}about' % NS.rdf]
        if subject is None:
            subject = about
        elif subject != about:
            raise ValueError('Statements about multiple subjects')
        for predicate in description:
            ns, tag = predicate.tag[1:].split('}')
            uri = predicate.attrib.get('{%s}resource' % NS.rdf)
            if uri:
                data = {'value': uri, 'type': 'uri'}
            else:
                data = {'value': predicate.text, 'type': 'literal'}
                lang = predicate.get('{%s}lang' % NSXML)
                datatype = predicate.get('{%s}datatype' % NS.rdf)
                if lang:
                    data['lang'] = lang
                elif datatype:
                    data['datatype'] = datatype
            result[ns+tag].append(data)
    return result
