from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='fcrepo',
    version='0.1',
    author='Infrae',
    author_email='jasper@infrae.com',
    description="API implementation for the Fedora Commons Repository platform",
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data = True,
    zip_safe=False,
    license='BSD',
    entry_points= {
    'console_scripts': [
        'install_fedora = fcrepo.tools:install_fedora',
        'start_fedora = fcrepo.tools:start_fedora',
      ]
    },
    install_requires=[
    'lxml',
    ],
)
