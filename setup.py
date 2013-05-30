

# http://docs.python.org/distutils/
# http://packages.python.org/distribute/
try:
    from setuptools import setup
except:
    from distutils.core import setup

setup(
    name = 'python-vxi11',
    description = 'Python VXI-11 driver for controlling instruments over Ethernet',
    version = '0.1',
    long_description = '''This Python package supports the VXI-11 Ethernet
instrument control protocol for controlling VXI11 and LXI compatible instruments.''',
    author = 'Alex Forencich',
    author_email = 'alex@alexforencich.com',
    url = 'http://alexforencich.com/wiki/en/python-vxi11/start',
    download_url = 'http://github.com/alexforencich/python-vxi11/tarball/master',
    keywords = 'VXI LXI measurement instrument',
    license = 'MIT License',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Hardware :: Hardware Drivers',
        'Topic :: System :: Networking',
        'Programming Language :: Python :: 3'
        ],
    packages = ['vxi11']
)

