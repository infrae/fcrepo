# Copyright (c) 2010 Infrae / Technical University Delft. All rights reserved.
# See also LICENSE.txt

import sys
import os
import subprocess
import tempfile
from ConfigParser import ConfigParser


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


def get_fedora_version():
    config = ConfigParser()
    config.read( os.path.join(os.getcwd(), 'buildout.cfg') )
    return config.get('buildout', 'extends').replace('profiles/', '')


def check_java_version():
    try:
        output = subprocess.Popen(['java','-version'],    
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT
                                 ).communicate()[0]
        java_version = (output.splitlines() or [''])[0]
        if not java_version.startswith('java version "1.6'):
            print >> sys.stderr, ('wrong version of java')
            sys.exit(1)
    except:
        print >> sys.stderr, ('java not installed')
        sys.exit(1)


def install_fedora():
    base_dir = os.path.join(os.getcwd(), 'parts')

    if get_fedora_version() == 'fedora-3.3.cfg':
        jarfile = os.path.join(base_dir, 'fc3.3', 'fcrepo-installer-3.3.jar')
        if not os.path.isfile(jarfile):
            print >> sys.stderr, ('fcrepo-installer-3.3.jar is missing, '
                                  'run buildout first')
            sys.exit(1)
        fedora_path = os.path.join(base_dir, 'fedora-3.3').replace('\\','/')

    elif get_fedora_version() == 'fedora-3.4.cfg':
        jarfile = os.path.join(base_dir, 'fc3.4', 'fcrepo-installer-3.4.jar')
        if not os.path.isfile(jarfile):
            print >> sys.stderr, ('fcrepo-installer-3.4444.jar is missing, '
                                  'run buildout first')
            sys.exit(1)
        fedora_path = os.path.join(base_dir, 'fedora-3.4').replace('\\','/')

    else:
        print >> sys.stderr, ('fcrepo-installer-3.3.jar or '
                              'fcrepo-installer-3.4.jar is missing, '
                              'run buildout first')
        sys.exit(1)

    check_java_version()
    
    install_props = FEDORA_INSTALL_PROPERTIES % {'host': FEDORA_HOST,
                                                 'port': FEDORA_PORT,
                                                 'passwd': FEDORA_PASSWD,
                                                 'path': fedora_path}
    fp = tempfile.NamedTemporaryFile(delete=False)
    fp.write(install_props)
    fp.close()
    os.system('java -jar "%s" "%s"' % (jarfile, fp.name))
    os.remove(fp.name)


def start_fedora():
    if get_fedora_version() == 'fedora-3.3.cfg':
        fedora_path = os.path.join(os.getcwd(), 'parts', 'fedora-3.3')
    elif get_fedora_version() == 'fedora-3.4.cfg':
        fedora_path = os.path.join(os.getcwd(), 'parts', 'fedora-3.4')
    else:
        print >> sys.stderr, ('Something went wrong, sorry...')
        sys.exit(1)

    if sys.platform.startswith('win'):
        os.environ['FEDORA_HOME'] = fedora_path
        os.environ['CATALINA_HOME'] = os.path.join(fedora_path,'tomcat')
        cmd = 'cmd /C "%CATALINA_HOME%\\bin\\catalina.bat" run'
    else:
        cmd = ('export FEDORA_HOME="%(path)s" && '
               'export CATALINA_HOME="%(path)s/tomcat" && '
               'sh "%(path)s/tomcat/bin/catalina.sh" run' % 
               {'path': fedora_path})
    os.system(cmd)

