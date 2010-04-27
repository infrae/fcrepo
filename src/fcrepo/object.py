# Copyright (c) 2010 Infrae / Technical University Delft. All rights reserved.
# See also LICENSE.txt

from fcrepo.datastream import FedoraDatastream, RELSEXTDatastream, DCDatastream

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
        if dsid == 'DC':
            return DCDatastream(dsid, self)
        elif dsid == 'RELS-EXT':
            return RELSEXTDatastream(dsid, self)
        else:
            return FedoraDatastream(dsid, self)

    def __delitem__(self, dsid):
        self.client.deleteDatastream(self.pid, dsid)
        self._dsids = None

    def delete(self, **params):
        self.client.deleteObject(self.pid, **params)
        
    def addDataStream(self, dsid, body='', **params):            
        self.client.addDatastream(self.pid, dsid, body, **params)
        self._dsids=None

    def methods(self):
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
