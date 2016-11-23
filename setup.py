"""
Fleaker
-------

Fleaker is a framework built on top of Flask that aims to make using Flask
easier and more productive, while promoting best practices.

Yes, it's BSD licensed.

Easier to Setup
`````````````

Save in an app.py:

.. code:: python

    import os

    from fleaker import App

    def create_app():
        app = App.create_app(__name__)
        settings_dict = {'DEBUG': True}
        app.configure('.settings', os.env, settings_dict)
        app.register_blueprints('.blueprints')

        return app

    if __name__ == '__main__':
        create_app().run()

Just as Easy to Use
```````````````````

Run it:

.. code:: bash

    $ pip install fleaker
    $ python app.py
     * Running on http://localhost:5000/
"""

import ast
import re

from setuptools import setup


_version_re = re.compile(r"__version__\s+=\s+(.*)")  # pylint: disable=invalid-name

with open('./fleaker/__init__.py', 'rb') as file_:
    version = ast.literal_eval(_version_re.search(  # pylint: disable=invalid-name
        file_.read().decode('utf-8')).group(1))

setup(name='fleaker',
      version=version,
      description='Tools and extensions to make Flask development easier.',
      url='https://github.com/croscon/fleaker',
      author='Croscon Consulting',
      author_email='hayden.chudy@croscon.com',
      license='BSD',
      packages=['fleaker'],
      zip_safe=False,
      long_description=__doc__,
      include_package_data=True,
      platforms='any',
      install_requires=[
          'Flask',
          'Flask-Classful',
          'Flask-Login',
          'Flask-Marshmallow',
          'marshmallow',
          # @TODO: We gotta be missing some things
          # pick one
          'peewee',
          'sqlalchemy',
      ],
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Web Environment',
          'Framework :: Flask',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          # @TODO: Pick specific Python versions; out of the gate flask does 2.6,
          # 2.7, 3.3, 3.4, and 3.5
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Software Development :: Libraries :: Application Frameworks',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ])
