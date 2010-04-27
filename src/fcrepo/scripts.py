# Copyright (c) 2010 Infrae / Technical University Delft. All rights reserved.
# See also LICENSE.txt

import sys
import os
import commands

FEDORA_INSTALL_PROPERTIES="""
ri.enabled=true
messaging.enabled=false
apia.auth.required=false
database.jdbcDriverClass=org.apache.derby.jdbc.EmbeddedDriver
ssl.available=false
database.jdbcURL=jdbc\:derby\:%(path)s/derby/fedora3;create\=true
database.password=fedoraAdmin
database.username=fedroaAdmin
tomcat.shutdown.port=8005
deploy.local.services=false
xacml.enabled=false
tomcat.http.port=%(port)s
fedora.serverHost=%(host)s
database=included
database.driver=included
fedora.serverContext=fedora
tomcat.home=%(path)s/tomcat
fedora.home=%(path)s
install.type=custom
fesl.enabled=false
servlet.engine=included
fedora.admin.pass=%(passwd)s"""

FEDORA_HOST = 'localhost'
FEDORA_PORT = '8080'
FEDORA_PASSWD = 'fedoraAdmin'

def install_fedora():
    jarfile = os.path.join(os.getcwd(), 'parts', 'java-dependencies',
                           'fcrepo-installer-3.3.jar')

    if not os.path.isfile(jarfile):
        print >> sys.stderr, ('fcrepo-installer-3.3.jar is missing, '
                              'run buildout first')
        sys.exit(1)

    java_version = (
        commands.getoutput('java -version').splitlines() or [''])[0]
    
    if not java_version.startswith('java version "1.6'):
        print >> sys.stderr, ('can not find java, or wrong version')
        sys.exit(1)
    
    fedora_path = os.path.join(os.getcwd(), 'parts', 'fedora')
    install_props = FEDORA_INSTALL_PROPERTIES % {'host': FEDORA_HOST,
                                                 'port': FEDORA_PORT,
                                                 'passwd': FEDORA_PASSWD,
                                                 'path': fedora_path}
    fp = open('/tmp/fedora_install.properties', 'w')
    fp.write(install_props)
    fp.close()

    os.system('java -jar "%s" /tmp/fedora_install.properties' % jarfile)

def start_fedora():
    fedora_path = os.path.join(os.getcwd(), 'parts', 'fedora')
    cmd = ('export FEDORA_HOME="%s" && export CATALINA_HOME="%s/tomcat" && '
           'sh "%s/tomcat/bin/catalina.sh" run' % (fedora_path,
                                                   fedora_path,
                                                   fedora_path))
    os.system(cmd)
