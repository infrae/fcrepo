from setuptools import setup, find_packages
from os.path import join, dirname

HISTORY = join(dirname(__file__), 'HISTORY.txt')
README = join(dirname(__file__), 'src', 'fcrepo', 'README.txt')

setup(
    name='fcrepo',
    version='1.0b2',
    author='Infrae / Jasper Op de Coul',
    author_email='jasper@infrae.com',
    description="API implementation for the Fedora Commons Repository platform",
    long_description=(open(README).read()+
                      '\n'+
                      open(HISTORY).read()),
    classifiers=["Development Status :: 4 - Beta",
                 "Programming Language :: Python",
                 "License :: OSI Approved :: BSD License",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 "Environment :: Web Environment",
                 "Intended Audience :: Science/Research"],

    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data = True,
    zip_safe=False,
    license='BSD',
    entry_points= {
    'console_scripts': [
        'install_fedora = fcrepo.scripts:install_fedora',
        'start_fedora = fcrepo.scripts:start_fedora',
      ]
    },
    install_requires=[
    'lxml',
    ],
)
