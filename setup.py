
from __future__ import with_statement

# http://docs.python.org/distutils/
# http://packages.python.org/distribute/
try:
    from setuptools import setup
except:
    from distutils.core import setup

import os.path

version_py = os.path.join(os.path.dirname(__file__), 'vxi11', 'version.py')
with open(version_py, 'r') as f:
    d = dict()
    exec(f.read(), d)
    version = d['__version__']

setup(
    name = 'python-vxi11',
    description = 'Python VXI-11 driver for controlling instruments over Ethernet',
    version = version,
    long_description = '''This Python package supports the VXI-11 Ethernet
instrument control protocol for controlling VXI11 and LXI compatible instruments.''',
    author = 'Alex Forencich',
    author_email = 'alex@alexforencich.com',
    url = 'http://alexforencich.com/wiki/en/python-vxi11/start',
    download_url = 'http://github.com/python-ivi/python-vxi11/tarball/master',
    keywords = 'VXI LXI measurement instrument',
    license = 'MIT License',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Hardware :: Hardware Drivers',
        'Topic :: System :: Networking',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'
        ],
    packages = ['vxi11'],
    entry_points = {
        'console_scripts': [
            'vxi11-cli = vxi11.cli:main',
        ],
    },
)

