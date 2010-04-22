
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
 
Note that you can't create a PID twice
  >>> obj = client.createObject(pid, label=u'Second try?')


