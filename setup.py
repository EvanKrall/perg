#!/usr/bin/python

from setuptools import setup, find_packages

setup(
    name='perg',
    version='0.0.1',
    description='Search code for patterns that match a given string',
    author='Evan Krall',
    author_email='evan@evankrall.com',
    packages=find_packages(),
    scripts=['perg/perg.py']
)