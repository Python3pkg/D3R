#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    "argparse",
    "lockfile",
    "psutil",
    "biopython",
    "xlsxwriter",
]

test_requirements = [
    "argparse",
    "lockfile",
    "psutil"
]

setup(
    name='d3r',
    version='0.5.1',
    description='Drug Design Data Resource CELPP Runner is an application to run the filtering, docking, and scoring '
                'of new sequences from wwpdb',
    long_description=readme + '\n\n' + history,
    author="Christopher Churas",
    author_email='churas@ncmir.ucsd.edu',
    url='https://github.com/nbcrrolls/D3R',
    packages=[
        'd3r', 'd3r.blast', 'd3r.filter', 'd3r.utilities'
    ],
    package_dir={'d3r':
                 'd3r'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='d3r',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.4',
    ],
    scripts = ['d3r/celpprunner.py', 'd3r/blastnfilter.py', 'd3r/postanalysis.py'],
    test_suite='tests',
    tests_require=test_requirements
)
