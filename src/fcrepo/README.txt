
FCRepo, a client for the Fedora Commons Repository
==================================================

Info
----

This package provides access to the `Fedora Commons Repository`_.

From the Fedora Commons Website:

     Fedora (Flexible Extensible Digital Object Repository Architecture) was originally developed by researchers at Cornell University as an architecture for storing, managing, and accessing digital content in the form of digital objects inspired by the `Kahn and Wilensky`_ Framework.  Fedora defines a set of abstractions for expressing digital objects, asserting relationships among digital objects, and linking "behaviors" (i.e., services) to digital objects. The Fedora Repository Project (i.e., Fedora) implements the Fedora abstractions in a robust open source software system. 

This package uses WADL, `Web Application Description Language`_ to parse the
WADL file that comes with Fedora so it offers support for the
complete REST API.
On top of that a more highlevel abstraction is written, which will be
demonstrated in this `doctest`_.
This package has been written for FedoraCommons 3.3, it has not been tested
with older versions. REST API documentation can be found in the `Fedora wiki`_.


This package can be installed using buildout which will also fetch the
Fedora installer, and install it locally for testing purposes. 
Use the following steps to install and run this doctest::

   python bootstrap.py
   ./bin/buildout
   ./bin/install_fedora
   ./bin/start_fedora
   ./bin/test

This software has been developed using python2.6 on a linux system. Other
platforms have not been tested at the moment.

.. _Fedora Commons Repository: http://www.fedora-commons.org/
.. _Kahn and Wilensky: http://www.cnri.reston.va.us/k-w.html
.. _Web Application Description Language: http://www.w3.org/Submission/wadl/
.. _Fedora wiki: http://www.fedora-commons.org/confluence/display/FCR30/REST+API
.. _doctest: http://en.wikipedia.org/wiki/Doctest
.. _REST API Documentation: http://www.fedora-commons.org/confluence/display/FCR30/REST+API

Using the fcrepo package
------------------------

Connecting to the Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To connect to the running Fedora, we first need a connection. The connection
code was largely copied from `Etienne Posthumus ("Epoz") duraspace module`_.

.. _Etienne Posthumus ("Epoz") duraspace module: http://bitbucket.org/epoz/duraspace

  >>> from fcrepo.connection import Connection
  >>> connection = Connection('http://localhost:8080/fedora', 
  ...                         username='fedoraAdmin', 
  ...                         password='fedoraAdmin')


Now that we have a connection, we can create a FedoraClient:

  >>> from fcrepo.client import FedoraClient
  >>> client = FedoraClient(connection)

PIDs
~~~~

A Fedora object needs a unique PID to function. The PID consists of a 
namespace string, then a semicolon and then a string identifier. 
You can create your own PIDs using a random UUID, but you can also use
the nextPID feature of Fedora which returns an ascending number.

  >>> pid = client.getNextPID(u'foo')
  >>> ns, num = pid.split(':')
  >>> ns == 'foo' and num.isdigit()
  True

We can also get multiple PIDs at once

  >>> pids = client.getNextPID(u'foo', numPIDs=10)
  >>> len(pids)
  10

This method returns unicode strings or a list of unicode strings if
multiple PIDs are requested. 

The client abstraction provides wrappers around the 'low-level' 
API code which is generated from the WADL file. 
Here's the same call through the WADL API:

  >>> print client.api.getNextPID().submit(namespace=u'foo', format=u'text/xml').read()
  <?xml  ...?>
  <pidList ...>
    <pid>...</pid>
  </pidList>

So the client methods call the methods from the WADL API, 
parse the resulting xml and uses sensible default arguments.

This is how most client method calls work. 
Normally you would never need to access the WADL API directly, 
so let's move on.

Creating Objects
~~~~~~~~~~~~~~~~

Now that we can get PIDs we can use them and create a new object:

  >>> pid = client.getNextPID(u'foo')
  >>> obj = client.createObject(pid, label=u'My First Test Object')
 
You can't create an object with the same PID twice.

  >>> obj = client.createObject(pid, label=u'Second try?')
  Traceback (most recent call last):
  ...
  FedoraConnectionException: ... The PID 'foo:...' already exists in the registry; the object can't be re-created.

Fetching Objects
~~~~~~~~~~~~~~~~

Off course it's also possible to retrieve an existing object with the client:

  >>> obj = client.getObject(pid)
  >>> print obj.label
  My First Test Object  

You'll get an error if the object does not exist:

  >>> obj = client.getObject(u'foo:bar')
  Traceback (most recent call last):
  ...
  FedoraConnectionException: ...no path in db registry for [foo:bar]


Deleting Objects
~~~~~~~~~~~~~~~~

Deleting objects can be done by calling the delete method on an object,
or by passing the pid to the deleteObject method on the client.

  >>> pid = client.getNextPID(u'foo')
  >>> o = client.createObject(pid, label=u'About to be deleted')
  >>> o.delete(logMessage=u'Bye Bye')
  >>> o = client.getObject(pid)
  Traceback (most recent call last):
  ...
  FedoraConnectionException: ...no path in db registry for [foo:...]

Note that in most cases you don't want to delete an object. It's better to
set the state of the object to `deleted`. More about this in the next section.

Object Properties
~~~~~~~~~~~~~~~~~

In the previous examples we retrieved a Fedora object. 
These objects have a number of properties that can be get and set:

  >>> obj.label
  u'My First Test Object'
  >>> date = obj.lastModifiedDate
  >>> obj.label = u'Changed it!'

The last line modified the label property on the Fedora server, 
the lastmodified date should now have been updated:

  >>> obj.lastModifiedDate > date
  True
  >>> obj.label
  u'Changed it!'

Setting properties can also be used to change the state of a FedoraObject 
to inactive or deleted. The following strings can be used: 

  * `A` means active
  * `I` means inactive
  * `D` means deleted

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

Object DataStreams
~~~~~~~~~~~~~~~~~~

A Fedora object is basicly a container of Datastreams. You can iterate through 
the object to find the datastream ids or call the datastreams method:

  >>> print obj.datastreams()
  ['DC']
  >>> for id in obj: print id
  DC
  >>> 'DC' in obj
  True

To actually get a datastream we can access it as if it's a dictionary:
 
  >>> ds = obj['DC']
  >>> ds
  <fcrepo.datastream.DCDatastream object at ...>
  >>> obj['FOO']
  Traceback (most recent call last):
  ...
  FedoraConnectionException: ...No datastream could be found. Either there is no datastream for the digital object "..." with datastream ID of "FOO"  OR  there are no datastreams that match the specified date/time value of "null".

Datastream Properties
~~~~~~~~~~~~~~~~~~~~~

A datastream has many properties, including label, state and createdDate, just
like the Fedora object:

  >>> print ds.label
  Dublin Core Record for this object

  >>> print ds.state
  A

There are different types of datastreams, this one is of type `X`, which means
the content is stored inline in the `FOXML file`_ . FOXML is the internal 
storage format of Fedora.

.. _FOXML file: http://fedora-commons.org/confluence/display/FCR30/Introduction+to+FOXML


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

The location ID changes with every version, and old versions of the datastream
are still available. The fcrepo client code contains no methods to retrieve
old versions of datastreams or view the audit trail of objects. 
The methods that implement this are available in the WADL API though.

Fedora can create checksums of the content stored in a datastream, 
by default checksums are disabled, if we set the checksumType property
to MD5, Fedora will generate the checksum for us.

  >>> ds.checksumType  
  u'DISABLED'
  >>> ds.checksumType = u'MD5'
  >>> ds.checksum # the checksum always changes between tests
  u'...'

There are some additional properties, not all of them can be set.
Have a look at the `REST API Documentation`_ for a full list

  >>> ds.mimeType
  u'text/xml'
  >>> ds.size > 0
  True
  >>> ds.formatURI
  u'http://www.openarchives.org/OAI/2.0/oai_dc/'


Getting and Setting Content
~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can also get and set the content of the datastream:

  >>> xml = ds.getContent().read()
  >>> print xml
  <oai_dc:dc ...>
    <dc:title>My First Test Object</dc:title>
    <dc:identifier>foo:...</dc:identifier>
  </oai_dc:dc>

  >>> xml = xml.replace('My First Test Object', 'My First Modified Datastream')
  >>> ds.setContent(xml)

Special Datastream: DC
~~~~~~~~~~~~~~~~~~~~~~

This `DC` datastream that is always available is actually a special kind of 
datastream. The Dublin Core properties from this XML stream are stored in a
relational database which can be searched. The values are also used in the
OAIPMH feed. Fedora uses the legacy `/elements/1.1/` namespace which contains
the following terms:

 * contributor
 * coverage
 * creator
 * date
 * description
 * format
 * identifier
 * language
 * publisher
 * relation
 * rights
 * source
 * subject
 * title
 * type

View the `Dublin Core website`_ for a `description of these properties`_.

.. _description of these properties: http://dublincore.org/documents/dcmi-terms/#H3
.. _Dublin Core website: http://dublincore.org

Since editing the Dublin Core XML data by hand gets a bit cumbersome, 
the DC datastream allows access to the DC properties as if the datastream 
is a dictionary:

  >>> ds['title']
  [u'My First Modified Datastream']

This can also be used to set values:

  >>> ds['subject'] = [u'fcrepo', u'unittest']
  >>> ds['description'].append(u'A test object from the fcrepo unittest')

  >>> for prop in sorted(ds): print prop
  description
  identifier
  subject
  title
  >>> 'subject' in ds
  True
 

To save this, we call the setContent method again, but this time with no
arguments. This will make the code use the values from the dictionary to
generate the XML string for you

  >>> ds.setContent()
  >>> print ds.getContent().read()
  <oai_dc:dc ...>
    ...
    <dc:description>A test object from the fcrepo unittest</dc:description>
    ...
  </oai_dc:dc>

Inline XML Datastreams
~~~~~~~~~~~~~~~~~~~~~~

Let's try adding some datastreams, for example, we want to store some XML data:

  >>> obj.addDataStream('FOOXML', '<foo/>', 
  ...                   label=u'Foo XML', 
  ...                   logMessage=u'Added an XML Datastream')
  >>> obj.datastreams()
  ['DC', 'FOOXML']
  >>> print obj['FOOXML'].getContent().read()
  <foo></foo>

Managed Content Datastreams
~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can also add Managed Content, this will be stored and managed by fedora,
but it's not inline xml. The data is stored in a seperate file on 
the harddrive. We do this by setting the controlGroup param to `M`

  >>> obj.addDataStream('TEXT', 'Hello!', label=u'Some Text',
  ...                   mimeType=u'text/plain', controlGroup=u'M', 
  ...                   logMessage=u'Added some managed text')
  >>> obj.datastreams()
  ['DC', 'FOOXML', 'TEXT']
  >>> ds = obj['TEXT']
  >>> ds.size
  0
  >>> ds.getContent().read()
  'Hello!'

This is perfectly fine for small files, however when you don't want to hold
the whole file in memory you can also supply a file stream. Let's make a 3MB
file:

  >>> import tempfile, os
  >>> fd, filename = tempfile.mkstemp()
  >>> fp = open(filename, 'w')
  >>> fp.write('foo' * (1024**2))
  >>> fp.close()
  >>> os.path.getsize(filename)
  3145728

Now we'll open the file and stream it to Fedora. We then read the whole thing
in memory and see if it's the same size:

  >>> fp = open(filename, 'r')
  >>> ds.setContent(fp)
  >>> fp.close()
  >>> content = ds.getContent().read()
  >>> len(content)
  3145728
  >>> os.remove(filename)  

Externally Referenced Datastreams
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For large files it might not be convenient to store them inside Fedora. 
In this case the file can be hosted externally, and we store a datastream
of controlGroup type `E` (Externally referenced)

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
redirects. This datastream has controlGroup `R` (Redirect Referenced)

  >>> obj.addDataStream('HOMEPAGE', controlGroup=u'R',
  ...                   location=u'http://pypi.python.org/fcrepo')
  >>> obj.datastreams()
  ['DC', 'FOOXML', 'TEXT', 'URL', 'HOMEPAGE']

This datastream works the same as an externally referenced stream. 

Deleting Datastreams
~~~~~~~~~~~~~~~~~~~~

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

Another Special Datastream: RELS-EXT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Besides the special `DC` datastream, there is another special datastream 
called `RELS-EXT`.
This datastream should contain `flat` RDFXML data which will be indexed in a
triplestore. The `RELS-EXT` datastream has some additional methods to assist in 
working with the RDF data.

To create the RELS-EXT stream we don't need to supply an RDFXML file, it will
create an empty one if no data is send.

  >>> obj.addDataStream('RELS-EXT')
  >>> ds = obj['RELS-EXT']

Now we can add some RDF data. Each predicate contains a list of values, each
value is a dictionary with a value and type key, and optionally a lang and
datatype key. This is identical to the `RDF+JSON format`_.

.. _RDF+JSON format: http://n2.talis.com/wiki/RDF_JSON_Specification

  >>> from fcrepo.utils import NS
  >>> ds[NS.rdfs.comment].append(
  ...       {'value': u'A Comment set in RDF', 'type': u'literal'})
  >>> ds[NS.rdfs.comment]
  [{'type': u'literal', 'value': u'A Comment set in RDF'}]
  >>> NS.rdfs.comment in ds
  True
  >>> for predicate in ds: print predicate
  http://www.w3.org/2000/01/rdf-schema#comment

To save this we call the setContent method without any data. 
This will serialise the RDF statements to RDFXML and perform the save action:
   
  >>> ds.setContent()
  >>> print ds.getContent().read()
  <rdf:RDF ...>
    <rdf:Description rdf:about="info:fedora/foo:...">
      <rdfs:comment>A Comment set in RDF</rdfs:comment>
    </rdf:Description>
  </rdf:RDF>

We are not allowed to add statements using the `DC` namespace.
This will result in an error. I suppose this is because it should be set 
through the `DC` datastream.

  >>> ds[NS.dc.title].append({'value': u'A title', 'type': 'literal'})
  >>> ds.setContent()
  Traceback (most recent call last):
  ...
  FedoraConnectionException: ... The RELS-EXT datastream has improper relationship assertion: dc:title.

We can also use RDF to create relations between objects. For example we can add
a relation using the Fedora isMemberOfCollection which can be used to group
objects into collections that are used in the OAIPMH feed.

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

  >>> print ds.predicates()
  ['http://www.w3.org/2000/01/rdf-schema#comment', 'info:fedora/fedora-system:def/relations-external#isMemberOfCollection']

Notice that the Fedora PID needs to be converted to an URI before it can be
referenced in RDF, this is done by prepending `info:fedora/` to the PID.

Service Definitions and Object Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Besides datastreams, a Fedora object can have methods registered to it through
service definitions. We don't provide direct access to the service definitions
but assume that all the methods have unique names.

  >>> obj.methods()
  ['viewObjectProfile', 'viewMethodIndex', 'viewItemIndex', 'viewDublinCore']

  >>> print obj.call('viewDublinCore').read()
  <html ...>
  ...
  <td ...>My First Modified Datastream</td>
  ...
  </html>

Searching Objects
~~~~~~~~~~~~~~~~~

Fedora comes with simple search functionality based on data from 
the `DC` datastream and the Fedora object properties.
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

A condition is a field (choose from the field names above) followed by an operator, followed by a value.

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

So let's create 5 objects which we can use to search on:

   >>> pids = pids = client.getNextPID(u'searchtest', numPIDs=5)
   >>> for pid in pids: client.createObject(pid, label=u'Search Test Object')
   <fcrepo.object.FedoraObject object at ...>
   <fcrepo.object.FedoraObject object at ...>
   <fcrepo.object.FedoraObject object at ...>
   <fcrepo.object.FedoraObject object at ...>
   <fcrepo.object.FedoraObject object at ...>

Now we'll search for these objects with a pid search, we also want the label
returned from the search.

   >>> client.searchObjects(u'pid~searchtest:*', ['pid', 'label'])
   <generator object searchObjects at ...>

The search returns a generator, by default it queries the server for the
first 10 objects, but if you iterate through the resultset and come to the end
the next batch will automatically be added. 

To illustrate this we will query with a batch size of 2:

   >>> results = client.searchObjects(u'pid~searchtest:*', ['pid', 'label'],
   ...                                maxResults=2)
   >>> result_list = [r for r in results]
   >>> len(result_list) >= 5
   True
   >>> result_list[0]['pid']
   u'searchtest:...'
   >>> result_list[0]['label']
   u'Search Test Object'

As shown we actually get more results then the max of 2, but the client asks
Fedora for results in batches of 2 while we iterate through the results 
generator.

RDF Index Search
~~~~~~~~~~~~~~~~

Besides searching the DC datastream in the relational database, 
it's also possible to query the RELS-EXT datastream through the triplestore 
in the SPARQL language.

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

Other output formats and query languages can be specified as parameters, by
default only SPARQL is supported.

The searchTriples method also has a `flush` argument. 
If you change a RELS-EXT datastream in Fedora, the triplestore is actually not
updated! You have to set this flush param when you're searching to `true` to
make sure the triplestore is updated. By default Fedora sets the flush 
parameter to `false` which is understandable for performance reasons but 
can be very confusing.
This library sets the param to `true` by default, which is not always very 
efficient, but you are sure the triplestore is up to date.

