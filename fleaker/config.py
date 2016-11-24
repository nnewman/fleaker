# ~*~ coding: utf-8 ~*~
"""
fleaker.config
~~~~~~~~~~~~~~

This module implements various utilities for configuring your Fleaker
:class:`App`.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import importlib
import os
import types

from os.path import splitext

import flask

from ._compat import string_types


class MultiStageConfigurableApp(flask.Flask):
    """The :class:`MultiStageConfigurableApp` is a mixin used to provide the
    primary ``configure`` method used to configure a `Fleaker` :class:`App`.

    .. versionadded:: 0.1.0
       The :class:`MultiStageConfigurableApp` class has existed since Fleaker
       was conceived.
    """

    def configure(self, *args, **kwargs):
        """Configure the Application through a varied number of sources of
        different types.

        This function chains multiple possible configuration methods together
        in order to just "make it work". You can pass multiple configuration
        sources in to the method and each one will be tried in a sane fashion.
        Later sources will override earlier sources if keys collide. For
        example:

        .. code:: python
            from application import default_config
            app.configure(default_config, os.environ, '.secrets')

        In the above example, values stored in ``default_config`` will be
        loaded first, then overwritten by those in ``os.environ``, and so on.

        An endless number of configuration sources may be passed.

        Configuration sources are type checked and processed according to the
        following rules:

        * ``string`` - if the source is a ``str``, we will assume it is a file
          or module that should be loaded. If the file ends in ``.json``, then
          :method:`flask.Config.from_json` is used; if the file ends in ``.py``
          or ``.cfg``, then :method:`flask.Config.from_pyfile` is used; if the
          module has any other extension we assume it is an import path, import
          the module and pass that to :method:`flask.Config.from_object`. See
          below for a few more semantics on module loading.
        * ``dict-like`` - if the source is ``dict-like``, then
          :method:`flask.Config.from_mapping` will be used. ``dict-like`` is
          defined as anything implementing an ``items`` method that returns
          a tuple of ``key``, ``val``.
        * ``class`` or ``module`` - if the source is an uninstantiated
          ``class`` or ``module``, then :method:`flask.Config.from_object` will
          be used.

        Just like Flask's standard configuration, only uppercased keys will be
        loaded into the config.

        If the item we are passed is a ``string`` and it is determined to be
        a possilbe Python module, then a leading ``.`` is relevant. If
        a leading ``.`` is provided, we assume that the module to import is
        located in the current package and operate as such; if it begins with
        anything else we assume the import path provided is absolute. This
        allows you to source configuration stored in a module in your package,
        or in another package.

        Args:
            *args (object): Any object you want us to try to configure from.

        Kwargs:
            whitelist_keys_from_mappings (bool): Should we whitelist the keys
                we pull from mappings? Very useful if you're passing in an
                entire OS environ and you want to omit things like
                ``LESSPIPE``. If no whitelist is provided, we use the
                pre-existing config keys as a whitelist.
            whitelist (list[str]): An explicit list of keys that should be
                allowed. If provided and ``whitelist_keys`` is true, we will
                use that as our whitelist instead of pre-existing app config
                keys.
        """
        whitelist_keys_from_mappings = kwargs.get(
            'whitelist_keys_from_mappings', False
        )
        whitelist = kwargs.get('whitelist')

        for item in args:
            if isinstance(item, string_types):
                _, ext = splitext(item)

                if ext == '.json':
                    self._configure_from_json(item)
                elif ext in ('.cfg', '.py'):
                    self._configure_from_pyfile(item)
                else:
                    self._configure_from_module(item)

            elif isinstance(item, (types.ModuleType, type)):
                self._configure_from_object(item)

            elif hasattr(item, 'items'):
                # assume everything else is a mapping like object; ``.items()``
                # is what Flask uses under the hood for this method
                # @TODO: This doesn't handle the edge case of using a tuple of
                # two element tuples to config; but Flask does that. IMO, if
                # you do that, you're a monster.
                self._configure_from_mapping(
                    item,
                    whitelist_keys=whitelist_keys_from_mappings,
                    whitelist=whitelist
                )

            else:
                raise TypeError("Could not determine a valid type for this"
                                " configuration object: `{}`!".format(item))

    def _configure_from_json(self, item):
        """Load configuration from a JSON file.

        This method will essentially just ``json.load`` the file, grab the
        resulting object and pass that to ``_configure_from_object``.

        Args:
            items (str): The path to the JSON file to load.

        Returns:
            fleaker.App: Returns itself.
        """
        self.config.from_json(item)

        return self

    def _configure_from_pyfile(self, item):
        """Load configuration from a Python file. Python files include Python
        source files (``.py``) and ConfigParser files (``.cfg``).

        This behaves as if the file was imported and passed to
        ``_configure_from_object``.

        Args:
            items (str): The path to the Python file to load.

        Returns:
            fleaker.App: Returns itself.
        """
        self.config.from_pyfile(item)

        return self

    def _configure_from_module(self, item):
        """Configure from a module by import path.

        Effectively, you give this an absolute or relative import path, it will
        import it, and then pass the resulting object to
        ``_configure_from_object``.

        Args:
            item (str): A string pointing to a valid import path.

        Returns:
            fleaker.App: Returns itself.
        """
        package = None
        if item[0] == '.':
            package = self.import_name

        obj = importlib.import_module(item, package=package)

        self.config.from_object(obj)

        return self

    def _configure_from_mapping(self, item, whitelist_keys=False,
                                whitelist=None):
        """Configure from a mapping, or dict, like object.

        Args:
            item (dict): A dict-like object that we can pluck values from.

        Kwargs:
            whitelist_keys (bool): Should we whitelist the keys before adding
                them to the configuration? If no whitelist is provided, we use
                the pre-existing config keys as a whitelist.
            whitelist (list[str]): An explicit list of keys that should be
                allowed. If provided and ``whitelist_keys`` is true, we will
                use that as our whitelist instead of pre-existing app config
                keys.

        Returns:
            fleaker.App: Returns itself.
        """
        if whitelist is None:
            whitelist = self.config.keys()

        if whitelist_keys:
            item = {k: v for k, v in item.items() if k in whitelist}

        self.config.from_mapping(item)

        return self

    def _configure_from_object(self, item):
        """Configure from any Python object based on it's attributes.

        Args:
            item (object): Any other Python object that has attributes.

        Returns:
            fleaker.App: Returns itself.
        """
        self.config.from_object(item)

        return self

    def configure_from_environment(self, whitelist_keys=False, whitelist=None):
        """Configure from the entire set of available environment variables.

        This is really a shorthand for grabbing ``os.environ`` and passing to
        :method:`_configure_from_mapping`.

        As always, only uppercase keys are loaded.

        Kwargs:
            whitelist_keys (bool): Should we whitelist the keys by only pulling
                those that are already present in the config? Useful for
                avoiding adding things like ``LESSPIPE`` to your app config.
            whitelist (list[str]): An explicit list of keys that should be
                allowed. If provided and ``whitelist_keys`` is true, we will
                use that as our whitelist instead of pre-existing app config
                keys.

        Returns:
            fleaker.App: Returns itself.
        """
        self._configure_from_mapping(os.environ, whitelist_keys=whitelist_keys,
                                     whitelist=whitelist)

        return self
