#!/usr/bin/env python
# vim:fileencoding=utf-8

from setuptools import setup


setup(
        name='django-webfaction',
        version='1.0',
        packages=['webfaction'],
        author='Pavel Zhukov',
        author_email='gelios@gmail.com',
        description='Collection of tools to run django on webfaction more seamless',
        long_description = open('README.rst').read(),
        license='GPL',
        keywords='webfaction, django',
        url='http://bitbucket.org/zeus/webfaction/'
        )
