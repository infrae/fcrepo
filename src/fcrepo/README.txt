
Fedora Commons Repository API
=============================

This package provides access to the Fedora Commons Repository.

It uses WADL, Web Application Description Language to parse the
WADL file that comes with FedoraCommons so it offers support for the
complete REST API.
On top of that a more highlevel abstraction is written, which will be
demonstrated in this doctest.

This package can be installed using buildout which will also fetch 
FedoraCommons 3.3. Use the following steps to install and run this doctest:

  python bootstrap.py
  ./bin/buildout
  ./bin/install_fedora
  ./bin/start_fedora
  ./bin/test

Connecting
----------

To connect to the running Fedora, we first need a connection. This code was
mainly copied from "Epoz" duraspace module.

  >>> from fcrepo.connection import Connection
  >>> connection = Connection('http://localhost:8080/fedora', 
  ...                         username='fedoraAdmin', 
  ...                         password='fedoraAdmin')


FedoraClient
------------

Now that we have a connection, we can create a FedoraClient

  >>> from fcrepo.client import FedoraClient
  >>> client = FedoraClient(connection)

The client provides wrappers around the 'raw' fedora REST API, 
for example we can use getNextPID to fetch one or more new ids:

  >>> pid = client.getNextPID(u'foo')
  >>> ns, num = pid.split(':')
  >>> ns == 'foo' and num.isdigit()
  True

We can also get multiple PIDs at once

  >>> pids = client.getNextPID(u'foo', numPIDs=10)
  >>> len(pids)
  10

This method returns unicode strings or a list of unicode strings if
multiple PIDs are requested. It wraps the getNextPID method from the
WADL API, parses the result xml and uses better default arguments.

Here's the same call through the WADL API:

  >>> print client.api.getNextPID().submit(namespace=u'foo', format=u'text/xml').read()
  <?xml  ...?>
  <pidList ...>
    <pid>...</pid>
  </pidList>

Now that we can get PIDs we can move on and create a new object

  >>> pid = client.getNextPID(u'foo')
  >>> obj = client.createObject(pid, label=u'My First Test Object')
 
Note that you can't create an object with the same PID twice.

  >>> obj = client.createObject(pid, label=u'Second try?')
  Traceback (most recent call last):
  ...
  FedoraConnectionException: ... The PID 'foo:...' already exists in the registry; the object can't be re-created.

It's also possible to fetch an object with the client

  >>> obj = client.getObject(pid)
  >>> print obj.label
  My First Test Object  

Deleting objects can be done by calling the delete method on an object,
or by passing the pid to the deleteObject method on the client.

  >>> pid = client.getNextPID(u'foo')
  >>> o = client.createObject(pid, label=u'About to be deleted')
  >>> o.delete()
  >>> o = client.getObject(pid)
  Traceback (most recent call last):
  ...
  FedoraConnectionException: ...no path in db registry for [foo:...]

FedoraObjects
-------------

Properties
~~~~~~~~~~

In the previous examples we retrieved a Fedora object. These objects have a number
of properties that can be get and set. 

  >>> date = obj.lastModifiedDate
  >>> obj.label = u'Changed it!'

This modified the label property on the Fedora server, the lastmodified date
should now have been updated:

  >>> obj.lastModifiedDate > date
  True
  >>> print obj.label
  Changed it!

This can also be used to set the state of a FedoraObject to inactive or deleted. 
The following strings can be used: 'A' means active, 'I' means inactive, 'D' means deleted.

  >>> obj.state = u'I'

Let's try a non supported state:

  >>> obj.state = u'Z'
  Traceback (most recent call last): 
  ...
  FedoraConnectionException: ... The object state of "Z" is invalid. The allowed values for state are:  A (active), D (deleted), and I (inactive).


Setting the modification or creation date directly results in an error, they can not be set.

  >>> obj.lastModifiedDate = date
  Traceback (most recent call last):
  ...
  AttributeError: can't set attribute

An ownerId can also be configured using the properties:

  >>> obj.ownerId = u'me'
  >>> print obj.ownerId
  me

DataStreams
~~~~~~~~~~~

A Fedora object is basicly a container of Datastreams. You can iterate through 
the object to find the datastream ids or call the datastreams method:

  >>> print obj.datastreams()
  ['DC']
  >>> for id in obj: print id
  DC
  >>> 'DC' in obj
  True

To actually get a datastream we can access it as if it's a dictionary
 
  >>> ds = obj['DC']
  >>> obj['FOO']
  Traceback (most recent call last):
  ...
  FedoraConnectionException: ...No datastream could be found. Either there is no datastream for the digital object "..." with datastream ID of "FOO"  OR  there are no datastreams that match the specified date/time value of "null".

  
A datastream has many properties, including label, state and createdDate, just
like the Fedora object

  >>> print ds.label
  Dublin Core Record for this object

  >>> print ds.state
  A

There are different types of datastreams, this one is of type 'X', which means it's
stored inline in the FOXML file as XML.

  >>> print ds.controlGroup
  X

A datastream can be versionable, this can be turned on or off.

  >>> ds.versionable
  True

The datastream also has a location, which is composed of the object pid,
the datastream id, and the version number

  >>> ds.location
  u'foo:...+DC+DC1.0'

Let's change the label, and see what happens:

  >>> ds.label = u'Datastream Metadata'
  >>> ds.location
  u'foo:...+DC+DC.1'

  >>> ds.label = u'Datastream DC Metadata'
  >>> ds.location
  u'foo:...+DC+DC.2'

There are some additional properties, some can only be set:

  >>> ds.mimeType
  u'text/xml'
  >>> ds.size > 0
  True
  >>> ds.formatURI
  u'http://www.openarchives.org/OAI/2.0/oai_dc/'

We can also get and set the content of the datastream

  >>> xml = ds.getContent().read()
  >>> print xml
  <oai_dc:dc ...>
    <dc:title>My First Test Object</dc:title>
    <dc:identifier>foo:...</dc:identifier>
  </oai_dc:dc>

  >>> xml = xml.replace('My First Test Object', 'My First Modified Datastream')
  >>> ds.setContent(xml)
  >>> ds.location
  u'foo:...+DC+DC.3'

By default checksums are disabled, if we set it to MD5, Fedora will generate 
the checksum for us.

  >>> print ds.checksumType  
  DISABLED
  >>> ds.checksumType = u'MD5'
  >>> ds.checksum # the checksum always changes between tests
  u'...'

Let's try adding some datastreams, for example, we want to store some XML data:

  >>> obj.addDataStream('FOOXML', '<foo/>', 
  ...                   label=u'Foo XML', 
  ...                   logMessage=u'Added an XML Datastream')
  >>> obj.datastreams()
  ['DC', 'FOOXML']
  >>> print obj['FOOXML'].getContent().read()
  <foo></foo>

We can also add Managed Content, this will be stored and managed by fedora,
but it's not inline xml. The data is stored in a seperate file on 
the harddrive. We do this by setting the controlGroup param to 'M'

  >>> obj.addDataStream('TEXT', 'Hello!  ', label=u'Some Text',
  ...                   mimeType=u'text/plain', controlGroup=u'M', 
  ...                   logMessage=u'Added some managed text')
  >>> obj.datastreams()
  ['DC', 'FOOXML', 'TEXT']
  >>> ds = obj['TEXT']
  >>> ds.size
  0
  >>> print ds.getContent().read()
  Hello!

For large files it might not be convenient to store them inside Fedora. 
In this case the file can be hosted externally, and we store a datastream
of controlGroup type 'E' (Externally referenced)

  >>> obj.addDataStream('URL', controlGroup=u'E',
  ...                   location=u'http://pypi.python.org/fcrepo')
  >>> obj.datastreams()
  ['DC', 'FOOXML', 'TEXT', 'URL']

This datastream does not have any content, so trying to read the
content will result in an error

  >>> ds = obj['URL']
  >>> ds.getContent()
  Traceback (most recent call last):
  ...
  FedoraConnectionException:..."Error getting http://pypi.python.org/fcrepo"  .

We can get the location though:

  >>> ds.location
  u'http://pypi.python.org/fcrepo'

The last of the datastream types is an externally referenced stream that 
redirects. This datastream has controlGroup 'R' (Redirect Referenced)

  >>> obj.addDataStream('HOMEPAGE', controlGroup=u'R',
  ...                   location=u'http://pypi.python.org/fcrepo')
  >>> obj.datastreams()
  ['DC', 'FOOXML', 'TEXT', 'URL', 'HOMEPAGE']

This datastream works the same as an externally referenced stream. 


A datastream can be deleted by using the python del keyword on the object,
or by calling the delete method on a datastream.

  >>> len(obj.datastreams())
  5
  >>> ds = obj['HOMEPAGE']
  >>> ds.delete(logMessage=u'Removed Homepage DS')  
  >>> len(obj.datastreams())
  4
  >>> del obj['URL']
  >>> len(obj.datastreams())
  3

Special Datastreams
~~~~~~~~~~~~~~~~~~~

Besides the special 'DC' datastream which is always present, and is indexed
in a relational database, there is another special datastream called 
'RELS-EXT'.
This datastream should contain 'flat' RDFXML data which will be indexed in a
triplestore. The RELS-EXT datastream has some additional methods to assist in 
working with the RDF data.

To create the RELS-EXT stream we don't need to supply an RDFXML file, it will
create an empty one if no data is send.

  >>> obj.addDataStream('RELS-EXT')
  >>> ds = obj['RELS-EXT']

Now we can add some RDF data. Each predicate contains a list of values, each
value is a dictionary with a value and type key, and optionally a lang and
datatype key. This is identical to the RDFJSON format.

  >>> from fcrepo.utils import NS
  >>> ds[NS.rdfs.comment].append(
  ...       {'value': u'A Comment set in RDF', 'type': u'literal'})
  >>> ds[NS.rdfs.comment]
  [{'type': u'literal', 'value': u'A Comment set in RDF'}]
  >>> NS.rdfs.comment in ds
  True
  >>> for predicate in ds: print predicate
  http://www.w3.org/2000/01/rdf-schema#comment

To save this we call setContent without any data. This will serialise the
RDF statements to RDFXML and perform the save action
   
  >>> ds.setContent()
  >>> print ds.getContent().read()
  <rdf:RDF ...>
    <rdf:Description rdf:about="info:fedora/foo:...">
      <rdfs:comment>A Comment set in RDF</rdfs:comment>
    </rdf:Description>
  </rdf:RDF>

Note that we are not allowed to add statements using the DC namespace.
This will result in an error. I suppose this is because we should set it
in the DC datastream.

  >>> ds[NS.dc.title].append({'value': u'A title', 'type': 'literal'})
  >>> ds.setContent()
  Traceback (most recent call last):
  ...
  FedoraConnectionException: ... The RELS-EXT datastream has improper relationship assertion: dc:title.

We can also use RDF to create relations between objects.

  >>> colpid = client.getNextPID(u'foo')
  >>> collection = client.createObject(colpid, label=u'A test Collection')
  >>> ds[NS.fedora.isMemberOfCollection].append(
  ...  {'value': u'info:fedora/%s' % colpid, 'type':u'uri'})
  >>> ds.setContent()
  >>> print ds.getContent().read()
  <rdf:RDF ...>
    <rdf:Description rdf:about="info:fedora/foo:...">
      <fedora:isMemberOfCollection rdf:resource="info:fedora/foo:..."></fedora:isMemberOfCollection>
      <rdfs:comment>A Comment set in RDF</rdfs:comment>
    </rdf:Description>
  </rdf:RDF>

Notice that the Fedora PID needs to be converted to an URI before it can be
referenced in RDF, this is done by prepending 'info:fedora/' to the PID.

  >>> print ds.predicates()
  ['http://www.w3.org/2000/01/rdf-schema#comment', 'info:fedora/fedora-system:def/relations-external#isMemberOfCollection']

Service Definitions and Object Methods
--------------------------------------

Besides datastreams, a Fedora object can have methods registered to it through
service definitions. We don't provide access to the service definitions and
assume that all the methods have unique names

  >>> obj.methods()
  ['viewObjectProfile', 'viewMethodIndex', 'viewItemIndex', 'viewDublinCore']

  >>> print obj.call('viewDublinCore').read()
  <html ...>
  ...
  <td ...>My First Modified Datastream</td>
  ...
  </html>

Searching Objects
-----------------

Fedora comes with simple search functionality based on the DC datastream.
The following properties can be used to search on:

 * cDate  
 * contributor     
 * coverage        
 * creator 
 * date    
 * dcmDate 
 * description     
 * format  
 * identifier      
 * label   
 * language        
 * mDate   
 * ownerId 
 * pid     
 * publisher       
 * source  
 * state   
 * subject 
 * title   
 * type    
 * rights

Fedora has a query syntax where you can enter one or more conditions, separated by space.  Objects matching all conditions will be returned.
A condition is a field (choose from the field names on the left) followed by an operator, followed by a value.
The = operator will match if the field's entire value matches the value given.
The ~ operator will match on phrases within fields, and accepts the ? and * wildcards.
The <, >, <=, and >= operators can be used with numeric values, such as dates.

Examples:

  pid~demo:* description~fedora
    Matches all demo objects with a description containing the word fedora.

  cDate>=1976-03-04 creator~*n*
    Matches objects created on or after March 4th, 1976 where at least one of the creators has an n in their name.

  mDate>2002-10-2 mDate<2002-10-2T12:00:00
    Matches objects modified sometime before noon (UTC) on October 2nd, 2002

So let's create 5 objects which we can use to search on

   >>> pids = pids = client.getNextPID(u'search', numPIDs=5)
   >>> for pid in pids: client.createObject(pid, label=u'Search Test Object')
   <fcrepo.client.FedoraObject object at ...>
   <fcrepo.client.FedoraObject object at ...>
   <fcrepo.client.FedoraObject object at ...>
   <fcrepo.client.FedoraObject object at ...>
   <fcrepo.client.FedoraObject object at ...>

Now we'll search for these objects with a pid search, we also want the label
returned from the search.

   >>> client.searchObjects(u'pid~search:*', ['pid', 'label'])
   <generator object searchObjects at ...>

The search returns a generator, by default it queries the server for the
first 10 objects, but if you iterate through the resultset and come to the end
the next batch will automatically be added. To illustrate we will query with
a batch size of 2

   >>> results = client.searchObjects(u'pid~search:*', ['pid', 'label'],
   ...                                maxResults=2)
   >>> result_list = [r for r in results]
   >>> len(result_list) >= 5
   True
   >>> result_list[0]['pid']
   u'search:...'
   >>> result_list[0]['label']
   u'Search Test Object'

RDF Index Search
----------------

Besides search the DC datastream in the relational database, it's also possible
to query the RELS-EXT datastream through the triplestore in the SPARQL 
language.

Let's find all objects that are part of the collection we created above in the
RELS-EXT datastream example

   >>> sparql = '''prefix fedora: <%s>
   ... select ?s where {?s fedora:isMemberOfCollection <info:fedora/%s>.}
   ... ''' % (NS.fedora, colpid)
   >>> result = client.searchTriples(sparql)
   >>> result
   <generator object searchTriples  at ...>
   >>> result = list(result)
   >>> len(result)
   1
   >>> result[0]['s']['value']
   u'info:fedora/foo:...'


   
