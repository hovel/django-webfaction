#!/usr/bin/env python
# vim:fileencoding=utf-8

from setuptools import setup, find_packages


setup(
        name='django-webfaction',
        version='2.0.1',
        packages=find_packages(),
        author='Pavel Zhukov',
        author_email='gelios@gmail.com',
        description='Collection of tools to run django on webfaction more seamless',
        long_description = open('README.rst').read(),
        license='GPL',
        keywords='webfaction, django',
        url='https://github.com/hovel/django-webfaction',
        include_package_data = True,
        install_requires = [
            'argparse',
            'keyring',
            'texttable',
        ],
        entry_points = {
            'console_scripts': [
                'webfactionctl = webfactionctl:main'
            ]
        }
)
