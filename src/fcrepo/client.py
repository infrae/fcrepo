from lxml import etree
from lxml.builder import ElementMaker

from fcrepo.wadl import API

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

    def updateObject(self, pid, body='', **kwargs):
        request = self.api.updateObject(pid=pid)
        response = request.submit(body, **kwargs)
        
    def listDatastreams(self, pid):
        request = self.api.listDatastreams(pid=pid)
        response = request.submit(format=u'text/xml')
        xml = response.read()
        response.close()
        doc = etree.fromstring(xml)
        return doc.xpath('/objectDatastreams/datastream/@dsid')

    def addDatastream(self, pid, dsid, body='', **params):

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

    def addDataStream(self, dsid, body='', **params):            
        self.client.addDatastream(self.pid, dsid, body, **params)
        self._dsids=None
        
class FedoraDataStream(object):
    def __init__(self, dsid, object):
        self.object = object
        self.dsid = dsid

        self._info = self.object.client.getDatastreamProfile(self.object.pid,
                                                             self.dsid)


    def getContent(self):
        return self.object.client.getDatastream(self.object.pid, self.dsid)

    def setContent(self, data, **kwargs):
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
