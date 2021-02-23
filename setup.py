#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements =  ["lxml"]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Sourabh Shrishrimal",
    author_email='sourabhshrishrimal@gmail.com',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Convert pdf documents into json object. It provides additional methods for searching within the document using regex and returns the found text with bounding box information",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='serialize_pdf',
    name='serialize_pdf',
    packages=find_packages(include=['serialize_pdf', 'serialize_pdf.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/crazycloud/serialize_pdf',
    version='0.1.0',
    zip_safe=False,
)
