#!/usr/bin/env python

from setuptools import setup, find_packages
setup(name='ansible_template_checker',
      version='0.2',
      description='pre-commit to check ansible templates for basic typos',
      packages=['ansible_template_checker'],
      include_package_data=True,
      zip_safe=False,
      install_requires=['jinja2', 'ansible'],
      entry_points={
          'console_scripts': [
              'ansible_template_checker=ansible_template_checker.cli:main'
          ]
      },
      )
