
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
  >>> ds.size
  381
  >>> ds.formatURI
  u'http://www.openarchives.org/OAI/2.0/oai_dc/'

We can also get and get the content of the datastream

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
but it's not inline xml. We do this by setting the controlGroup param to 'M'

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
