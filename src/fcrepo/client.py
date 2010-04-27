# Copyright (c) 2010 Infrae / Technical University Delft. All rights reserved.
# See also LICENSE.txt

import urllib

from lxml import etree
from lxml.builder import ElementMaker

from fcrepo.wadl import API
from fcrepo.utils import NS
from fcrepo.object import FedoraObject

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
        if not 'mimeType' in params:
            params['mimeType'] = u'application/binary'
            
        if 'checksumType' not in params:
            params['checksumType'] = u'MD5'

        params = self._fix_ds_params(params)

        request = self.api.addDatastream(pid=pid, dsID=dsid)
        request.headers['Content-Type'] = params['mimeType']
        response = request.submit(body, **params)        

    def _fix_ds_params(self, params):
        for name, param in params.items():
            newname = {'label': 'dsLabel',
                       'location': 'dsLocation',
                       'state': 'dsState'}.get(name, name)
            if newname != name:
                params[newname] = param
                del params[name]
                
        return params
        
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

    def modifyDatastream(self, pid, dsid, body='', **params):
        params = self._fix_ds_params(params)
        request = self.api.modifyDatastream(pid=pid, dsID=dsid)
        response = request.submit(body, **params)
        
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
                      limit=100, type='tuples', dt='on', flush=True):
        flush = str(flush).lower()
        url = u'/risearch?%s' % urllib.urlencode({'query':query,
                                                  'lang':lang,
                                                  'flush': flush,
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
        
