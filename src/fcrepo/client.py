import urllib
from collections import defaultdict

from lxml import etree
from lxml.builder import ElementMaker

from fcrepo.wadl import API
from fcrepo.utils import NS, dict2rdfxml, rdfxml2dict

NSMAP = {'foxml': 'info:fedora/fedora-system:def/foxml#'}

class FedoraClient(object):
    def __init__(self, connection):
        self.api = API(connection)

    def getNextPID(self, namespace, numPIDs=1, format=u'text/xml'):
        request = self.api.getNextPID()
        response = request.submit(namespace=namespace,
                                  numPIDs=numPIDs,
                                  format=format)
        xml = response.read()
        response.close()
        doc = etree.fromstring(xml)
        ids = [id.decode('utf8') for id in doc.xpath('/pidList/pid/text()')]
        if len(ids) == 1:
            return ids[0]
        return ids
        
    def createObject(self, pid, label, state=u'A'):
        foxml = ElementMaker(namespace=NSMAP['foxml'], nsmap=NSMAP)
        foxml_state = {'A': u'Active',
                       'I': u'Inactive',
                       'D': u'Deleted'}[state]
        doc = foxml.digitalObject(
            foxml.objectProperties(
              foxml.property(NAME="info:fedora/fedora-system:def/model#state",
                             VALUE=state),
              foxml.property(NAME="info:fedora/fedora-system:def/model#label",
                             VALUE=label)
              ),
            VERSION='1.1', PID=pid)
        body = etree.tostring(doc, encoding="UTF-8", xml_declaration=False)
        
        # add some newlines otherwise fedora xml parser will barf, also note
        # that xml_declarations are also not allowed (wtf?)
        body += '\r\n'
        
        request = self.api.createObject(pid=pid)
        request.headers['Content-Type'] = 'text/xml; charset=utf-8'
        response = request.submit(body, state=state[0], label=label)
        return self.getObject(pid)
    
    def getObject(self, pid):
        return FedoraObject(pid, self)

    def getObjectProfile(self, pid):
        request = self.api.getObjectProfile(pid=pid)
        response = request.submit(format=u'text/xml')
        xml = response.read()
        response.close()
        doc = etree.fromstring(xml)
        result = {'ownerId': u''}
        for child in doc:
            # rename elementnames to match property names in foxml
            name = {'objLabel': 'label',
                    'objOwnerId': 'ownerId',
                    'objCreateDate': 'createdDate',
                    'objLastModDate': 'lastModifiedDate',
                    'objState': 'state'}.get(child.tag)
            if name is None or child.text is None:
                continue
            value = child.text
            if not isinstance(value, unicode):
                value = value.decode('utf8')
            result[name] = value
        return result

    def updateObject(self, pid, body='', **params):
        request = self.api.updateObject(pid=pid)
        response = request.submit(body, **params)

    def deleteObject(self, pid, **params):
        request = self.api.deleteObject(pid=pid)
        response = request.submit(**params)
        
    def listDatastreams(self, pid):
        request = self.api.listDatastreams(pid=pid)
        response = request.submit(format=u'text/xml')
        xml = response.read()
        response.close()
        doc = etree.fromstring(xml)
        return doc.xpath('/objectDatastreams/datastream/@dsid')

    def addDatastream(self, pid, dsid, body='', **params):
        if dsid == 'RELS-EXT' and not body:
            body = ('<rdf:RDF xmlns:rdf="%s"/>' % NS.rdf)
            params['mimeType'] = u'application/rdf+xml'
            params['formatURI'] = (
                u'info:fedora/fedora-system:FedoraRELSExt-1.0')
        if params.get('controlGroup', u'X') == u'X':
            if not 'mimeType' in params:
                params['mimeType'] = u'text/xml'
            body += '\r\n'
        for name, param in params.items():
            newname = {'label': 'dsLabel',
                       'location': 'dsLocation',
                       'state': 'dsState'}.get(name, name)
            if newname != name:
                params[newname] = param
                del params[name]
                
        if not 'mimeType' in params:
            params['mimeType'] = u'application/binary'
            
        if 'checksumType' not in params:
            params['checksumType'] = u'MD5'

        request = self.api.addDatastream(pid=pid, dsID=dsid)
        request.headers['Content-Type'] = params['mimeType']
        response = request.submit(body, **params)        
        
    def getDatastreamProfile(self, pid, dsid):
        request = self.api.getDatastreamProfile(pid=pid, dsID=dsid)
        response = request.submit(format=u'text/xml')
        xml = response.read()
        response.close()
        doc = etree.fromstring(xml)
        result = {}
        for child in doc:
            # rename elementnames to match property names in foxml
            name = {'dsLabel': 'label',
                    'dsVerionId': 'versionId',
                    'dsCreateDate': 'createdDate',
                    'dsState': 'state',
                    'dsMIME': 'mimeType',
                    'dsFormatURI': 'formatURI',
                    'dsControlGroup': 'controlGroup',
                    'dsSize': 'size',
                    'dsVersionable': 'versionable',
                    'dsInfoType': 'infoType',
                    'dsLocation': 'location',
                    'dsLocationType': 'locationType',
                    'dsChecksum': 'checksum',
                    'dsChecksumType': 'checksumType'}.get(child.tag)
            if name is None or child.text is None:
                continue
            value = child.text
            if not isinstance(value, unicode):
                value = value.decode('utf8')
            result[name] = value
        return result

    def modifyDatastream(self, pid, dsid, body='', **kwargs):
        request = self.api.modifyDatastream(pid=pid, dsID=dsid)
        response = request.submit(body, **kwargs)
        
    def getDatastream(self, pid, dsid):
        request = self.api.getDatastream(pid=pid, dsID=dsid)
        return request.submit()

    def deleteDatastream(self, pid, dsid, **params):
        request = self.api.deleteDatastream(pid=pid, dsID=dsid)
        return request.submit(**params)

    def getAllObjectMethods(self, pid, **params):
        params['format'] = u'text/xml'
        request = self.api.getAllObjectMethods(pid=pid)
        response = request.submit(**params)
        xml = response.read()
        doc = etree.fromstring(xml)
        method_list = []
        for sdef_el in doc:
            sdef = sdef_el.attrib['pid']
            for method_el in sdef_el:
                method = method_el.attrib['name']
                method_list.append((sdef, method))
        response.close()
        return method_list

    def invokeSDefMethodUsingGET(self, pid, sdef, method, **params):
        request = self.api.invokeSDefMethodUsingGET(pid=pid, sDef=sdef,
                                                    method=method)
        return request.submit(**params)

        
    def searchObjects(self, query, fields, maxResults=10):
        field_params = {}
        assert isinstance(fields, list)
        for field in fields:
            field_params[field] = u'true'
            
        token = True
        NS = 'http://www.fedora.info/definitions/1/0/types/'
        while token:
            if token is True:
                token = False
            request = self.api.searchObjects()
            request.undocumented_params = field_params

            if token:
                response = request.submit(query=query,
                                          sessionToken=token,
                                          maxResults=maxResults,
                                          resultFormat=u'text/xml')
            else:
                response = request.submit(query=query,
                                          maxResults=maxResults,
                                          resultFormat=u'text/xml')

            xml = response.read()
            response.close()
            doc = etree.fromstring(xml)
                
            tokens = doc.xpath('//f:token/text()', namespaces={'f': NS})
            if tokens:
                token = tokens[0].decode('utf8')
            else:
                token = False
            
            for result in doc.xpath('//f:objectFields', namespaces={'f': NS}):
                data = {}
                for child in result:
                    field_name = child.tag.split('}')[-1].decode('utf8')
                    value = child.text
                    if not isinstance(value, unicode):
                        value = value.decode('utf8')
                        data[field_name] = value
                yield data

                
    def searchTriples(self, query, lang='sparql', format='Sparql',
                      limit=100, type='tuples', dt='on'):
        url = u'/risearch?%s' % urllib.urlencode({'query':query,
                                                  'lang':lang,
                                                  'flush': 'true',
                                                  'format':format,
                                                  'limit':limit,
                                                  'type':type,
                                                  'dt':dt})
        headers = {'Accept:': 'text/xml'}
        response = self.api.connection.open(url, '', headers, method='POST')
        xml = response.read()
        doc = etree.fromstring(xml)
        NS = 'http://www.w3.org/2001/sw/DataAccess/rf1/result' # ouch, old!
        for result in doc.xpath('//sparql:result', namespaces={'sparql': NS}):
            data = {}
            for el in result:
                name = el.tag.split('}')[-1]
                value = {}
                uri = el.attrib.get('uri')
                if uri:
                    value['value'] = uri.decode('utf8')
                    value['type'] = 'uri'
                else:
                    value['type'] = 'literal'
                    if isinstance(el.text, unicode):
                        value['value'] = el.text
                    else:
                        value['value'] = el.text.decode('utf8')
                    datatype = el.attrib.get('datatype')
                    lang = el.attrib.get('lang')
                    if datatype:
                        value['datatype'] = datatype
                    elif lang:
                        value['lang'] = lang
                data[name] = value
            yield data
        
    
class typedproperty(property):
    def __init__(self, fget, fset=None, fdel=None, doc=None, pytype=None):
        # like a normal property, but converts types to/from strings
        def typed_get(self):
            if pytype is bool:
                return fget(self) == 'true'
            return pytype(fget(self))
        
        def typed_set(self, value):
            if pytype is bool:
                return fset(self, unicode(value).lower())
            else:
                return fset(self, unicode(value).lower())
            
        super(typedproperty, self).__init__(typed_get, typed_set, fdel, doc)
        
class FedoraObject(object):
    def __init__(self, pid, client):
        self.pid = pid
        self.client = client
        self._info = self.client.getObjectProfile(self.pid)
        self._dsids = None # load lazy
        self._methods = None
        
    def _setProperty(self, name, value):
        msg = u'Changed %s object property' % name
        kwargs = {name: value, 'logMessage': msg}
        self.client.updateObject(self.pid, **kwargs)
        self._info = self.client.getObjectProfile(self.pid)

    label = property(lambda self: self._info['label'],
                     lambda self, value: self._setProperty('label', value))
    ownerId = property(lambda self: self._info['ownerId'],
                       lambda self, value: self._setProperty('ownerId', value))
    state = property(lambda self: self._info['state'],
                           lambda self, value: self._setProperty('state',
                                                                 value))
    # read only
    createdDate = property(lambda self: self._info['createdDate'])
    lastModifiedDate = property(lambda self: self._info['lastModifiedDate'])

    def datastreams(self):
        if self._dsids is None:
            self._dsids = self.client.listDatastreams(self.pid)
        return self._dsids

    def __iter__(self):
        return iter(self.datastreams())
    
    def __in__(self, dsid):
        return dsid in self.datastreams()

    def __getitem__(self, dsid):
        return FedoraDataStream(dsid, self)

    def __delitem__(self, dsid):
        self.client.deleteDatastream(self.pid, dsid)
        self._dsids = None

    def delete(self, **params):
        self.client.deleteObject(self.pid, **params)
        
    def addDataStream(self, dsid, body='', **params):            
        self.client.addDatastream(self.pid, dsid, body, **params)
        self._dsids=None

    def methods(self):
        result = []
        if self._methods is None:
            self._methods = self.client.getAllObjectMethods(self.pid)
        return [m[1] for m in self._methods]

    def call(self, method_name, **params):
        for sdef, method in self._methods:
            if method == method_name:
                break
        else:
            raise KeyError('No such method: %s' % method_name)
        
        return self.client.invokeSDefMethodUsingGET(self.pid, sdef,
                                                    method, **params)
        
class FedoraDataStream(object):
    def __init__(self, dsid, object):
        self.object = object
        self.dsid = dsid
        self._rdf = None
        self._info = self.object.client.getDatastreamProfile(self.object.pid,
                                                             self.dsid)

    def _get_rdf(self):
        if not self.dsid == 'RELS-EXT':
            raise ValueError('Datastream has no RDF support')
        if self._rdf is None:
            rdfxml = self.getContent().read()
            self._rdf = rdfxml2dict(rdfxml)
        return self._rdf

        
    def delete(self, **params):
        self.object.client.deleteDatastream(self.object.pid,
                                            self.dsid,
                                            **params)
        self.object._dsids = None

    def getContent(self):
        return self.object.client.getDatastream(self.object.pid, self.dsid)

    def setContent(self, data='', **kwargs):
        if self.dsid == 'RELS-EXT' and not data:
            rdf = self._get_rdf()
            data = dict2rdfxml(self.object.pid, rdf)
            self._rdf = None
            
        if self._info['controlGroup'] == 'X':
            # for some reason we need to add 2 characters to the body
            # or we get a parsing error in fedora
            data += '\r\n'
        
        self.object.client.modifyDatastream(self.object.pid,
                                            self.dsid,
                                            data,
                                            **kwargs)
        self._info = self.object.client.getDatastreamProfile(self.object.pid,
                                                             self.dsid)
        
    def _setProperty(self, name, value):
        msg = u'Changed %s datastream property' % name
        name = {'label': 'dsLabel',
                'location': 'dsLocation',
                'state': 'dsState'}.get(name, name)
        kwargs = {name: value, 'logMessage': msg, 'ignoreContent': True}
        self.object.client.modifyDatastream(self.object.pid,
                                            self.dsid,
                                            **kwargs)
        self._info = self.object.client.getDatastreamProfile(self.object.pid,
                                                             self.dsid)

    label = property(lambda self: self._info['label'],
                     lambda self, value: self._setProperty('label', value))
    location = property(lambda self: self._info['location'],
                        lambda self, value: self._setProperty('location', value))
    state = property(lambda self: self._info['state'],
                           lambda self, value: self._setProperty('state',
                                                                 value))
    checksumType = property(lambda self: self._info['checksumType'],
                            lambda self, value: self._setProperty('checksumType',
                                                                 value))
    versionId = property(lambda self: self._info['versionId'],
                        lambda self, value: self._setProperty('versionId',
                                                              value)) 
    mimeType = property(lambda self: self._info['mimeType'],
                        lambda self, value: self._setProperty('mimeType',
                                                              value)) 
    formatURI = property(lambda self: self._info['formatURI'],
                         lambda self, value: self._setProperty('formatURI',
                                                               value)) 


    versionable = typedproperty(lambda self: self._info['versionable'],
                                lambda self, value: self._setProperty(
                                  'versionable', value), pytype=bool) 

    # read only
    createdDate = property(lambda self: self._info['createdDate'])
    controlGroup = property(lambda self: self._info['controlGroup'])
    size = typedproperty(lambda self: self._info['size'], pytype=int)
    checksum = property(lambda self: self._info['formatURI'])


    def __setitem__(self, key, value):
        rdf = self._get_rdf()
        rdf[key]=value
        
    def __getitem__(self, key):
        rdf = self._get_rdf()
        return rdf[key]
    
    def __delitem__(self, key):
        rdf = self._get_rdf()
        del rdf[key]

    def __contains__(self, key):
        rdf = self._get_rdf()
        return key in rdf

    def __iter__(self):
        rdf = self._get_rdf()
        return rdf.__iter__()

    def predicates(self):
        rdf = self._get_rdf()
        keys = rdf.keys()
        keys.sort()
        return keys
