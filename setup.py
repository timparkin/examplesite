from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='examplesite',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'adminish',
          'commerce',
          'notification',
      ],
      entry_points="""
      # -*- Entry points: -*-
[paste.app_factory]
main = examplesite.wsgiapp:make_app

[paste.app_install]
main = paste.script.appinstall:Installer
      """,
      test_suite="examplesite.tests",
      tests_require=['WebTest'],
      )
