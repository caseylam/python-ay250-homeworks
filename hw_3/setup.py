import sys
from setuptools import setup

VERSION = '0.0.3'
DESCRIPTION = 'CalCalc package.'

CLASSIFIERS = ['Development Status :: 3 - Alpha',
               'Intended Audience :: Education',
               'Topic :: Software Development :: Libraries :: Python Modules',
               'License :: OSI Approved :: BSD License',
               'Programming Language :: Python :: 3.9']

setup(name='calcalc',
      version=VERSION,
      description=DESCRIPTION,
      long_description=DESCRIPTION,
      long_description_content_type='text/x-rst',
      classifiers=CLASSIFIERS,
      author='Casey Lam',
      author_email='casey_lam@berkeley.edu',
      url='http://github.com/caseylam/calcalc',
      python_requires='>=3',
      license='BSD',
      keywords='homework',
      packages=['calcalc'],
      platforms=['any'],
      setup_requires=['pytest_runner'],
      tests_require=['pytest'])
