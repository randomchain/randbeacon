#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
]

setup_requirements = [
    # 'setuptools_scm',
    'pytest-runner',
]

test_requirements = ['pytest', ]

setup(
    author="deis1014f18",
    author_email='deis1014f18@cs.aau.dk',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="A randomness beacon",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    # include_package_data=True,
    # use_scm_version=True,
    keywords='randbeacon',
    name='randbeacon',
    packages=find_packages(include=['randbeacon']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/randomchain/randbeacon',
    zip_safe=False,
)
