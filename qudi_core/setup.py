# -*- coding: utf-8 -*-

import os
import sys
from setuptools import setup, find_namespace_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

with open('README.md', 'r') as file:
    long_description = file.read()

with open(os.path.join('.', 'qudi', 'core', 'VERSION.txt'), 'r') as file:
    version = file.read().strip()

unix_dep = ['entrypoints',
            'fysom',
            'GitPython',
            'jupyter',
            'jupytext',
            'lmfit',
            'matplotlib',
            'numpy',
            'pyqtgraph',
            'PySide2',
            'pyzmq',
            'rpyc',
            'ruamel.yaml',
            ]

windows_dep = ['entrypoints',
               'fysom',
               'GitPython',
               'jupyter',
               'jupytext',
               'lmfit',
               'matplotlib',
               'numpy',
               'pyqtgraph',
               'PySide2',
               'pyzmq',
               'rpyc',
               'ruamel.yaml',
               ]


class PrePostDevelopCommands(develop):
    """ Pre- and Post-installation script for development mode.
    """

    def run(self):
        # PUT YOUR PRE-INSTALL SCRIPT HERE or CALL A FUNCTION
        develop.run(self)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        try:
            from qudi.core.qudikernel import install_kernel
            install_kernel()
        except:
            pass


class PrePostInstallCommands(install):
    """ Pre- and Post-installation for installation mode.
    """

    def run(self):
        # PUT YOUR PRE-INSTALL SCRIPT HERE or CALL A FUNCTION
        install.run(self)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        try:
            from qudi.core.qudikernel import install_kernel
            install_kernel()
        except:
            pass


setup(name='qudi_core',
      version=version,
      packages=[pkg for pkg in find_namespace_packages() if not pkg.startswith('qudi.core.artwork')],
      package_data={'': ['LICENSE.txt', 'COPYRIGHT.txt', 'README.md'],
                    'qudi.core': ['VERSION.txt',
                                  'default.cfg',
                                  'artwork/logo/*',
                                  'artwork/icons/oxygen/*',
                                  'artwork/icons/oxygen/**/*.png',
                                  'artwork/icons/qudiTheme/*',
                                  'artwork/icons/qudiTheme/**/*.png',
                                  'artwork/logo/*.png',
                                  'artwork/logo/*.ico',
                                  'artwork/logo/*.txt',
                                  'artwork/styles/*.qss',
                                  'artwork/styles/*.txt',
                                  'artwork/styles/**/*.png',
                                  'artwork/styles/**/*.txt',
                                  ]
                    },
      description='A modular laboratory experiment management suite',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/Ulm-IQO/qudi',
      keywords=['diamond',
                'quantum',
                'confocal',
                'experiment',
                'lab',
                'laboratory',
                'instrumentation',
                'instrument',
                'modular'
                ],
      license='GPLv3',
      install_requires=windows_dep if sys.platform == 'win32' else unix_dep,
      python_requires='~=3.7',
      cmdclass={'develop': PrePostDevelopCommands, 'install': PrePostInstallCommands},
      entry_points={
          'console_scripts': ['qudi=qudi.runnable:main',
                              'qudi-config-editor=qudi.tools.config_editor.config_editor:main',
                              'qudi-uninstall-kernel=qudi.core.qudikernel:uninstall_kernel',
                              'qudi-install-kernel=qudi.core.qudikernel:install_kernel'
                              ]
      },
      zip_safe=False
      )