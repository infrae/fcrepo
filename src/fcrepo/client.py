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
        
    def createObject(self, pid, label, state='Active'):
        foxml = ElementMaker(namespace=NSMAP['foxml'], nsmap=NSMAP)
        doc = foxml.digitalObject(
            foxml.objectProperties(
              foxml.property(NAME="info:fedora/fedora-system:def/model#state",
                             VALUE=state),
              foxml.property(NAME="info:fedora/fedora-system:def/model#label",
                             VALUE=label)
              ),
            VERSION='1.1', PID=pid)
        body = etree.tostring(doc, encoding="UTF-8")
        request = self.api.createObject(pid)
        response = request.submit(body, state=state[0], label=label)
        
