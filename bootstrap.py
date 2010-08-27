##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Bootstrap a buildout-based project

Simply run this script in a directory containing a buildout.cfg.
The script accepts buildout command-line options, so you can
use the -c option to specify an alternate configuration file.

$Id: bootstrap.py 29371 2008-06-19 16:03:45Z sylvain $
"""

import os, os.path, shutil, sys, tempfile, urllib2

tmpeggs = tempfile.mkdtemp()

enable_virtualenv = False
if '--virtualenv' in sys.argv:
    enable_virtualenv = True
    sys.argv.remove('--virtualenv')

if '--buildout-profile' in sys.argv:
    index = sys.argv.index('--buildout-profile') + 1
    if index > len(sys.argv):
        raise ValueError, '--buildout-profile require a config file.'
    buildout_config = sys.argv[index]
    if not os.path.isfile(buildout_config):
        raise ValueError, 'no such configuration file.'

    print "Creating configuration '%s'" % os.path.abspath('buildout.cfg')
    config = open('buildout.cfg', 'w')
    config.write("""[buildout]
extends = %s
""" % buildout_config)
    del config

    sys.argv.remove('--buildout-profile')
    sys.argv.remove(buildout_config)


if sys.platform.startswith('win'):
    bin_dir = 'Scripts'
else:
    bin_dir = 'bin'
python_path = os.path.join(bin_dir, os.path.basename(sys.executable))

try:
    import pkg_resources
except ImportError:
    ez = {}
    exec urllib2.urlopen('http://peak.telecommunity.com/dist/ez_setup.py'
                         ).read() in ez
    ez['use_setuptools'](to_dir=tmpeggs, download_delay=0)

    import pkg_resources

cmd = 'from setuptools.command.easy_install import main; main()'
if sys.platform == 'win32':
    cmd = '"%s"' % cmd # work around spawn lamosity on windows

ws = pkg_resources.working_set
assert os.spawnle(
    os.P_WAIT, sys.executable, sys.executable,
    '-c', cmd, '-mqNxd', tmpeggs, 'zc.buildout', 'virtualenv',
    dict(os.environ,
         PYTHONPATH=
         ws.find(pkg_resources.Requirement.parse('setuptools')).location
         ),
    ) == 0

ws.add_entry(tmpeggs)
if enable_virtualenv and not os.path.isfile(python_path):
    ws.require('virtualenv')
    import virtualenv
    from subprocess import call
    args = sys.argv[:]
    sys.argv = [sys.argv[0], os.getcwd(), '--clear', '--no-site-package']
    virtualenv.main()
    call(python_path + ' ' + ' '.join(args), shell=True)
    sys.exit(0)
    print 'exit'

ws.require('zc.buildout')
import zc.buildout.buildout
zc.buildout.buildout.main(sys.argv[1:] + ['bootstrap'])
shutil.rmtree(tmpeggs)
