#!/usr/bin/env python

import os

from setuptools import setup, find_packages

VERSION = '0.3.0'

if __name__ == '__main__':
    setup(
        name='dsc-it100',
        version=VERSION,
        description="A Python driver for the DSC IT-100 integration module.",
        long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
        author='Jernej Kos',
        author_email='jernej@kos.mx',
        url='https://github.com/kostko/dsc-it100',
        license='AGPLv3',
        packages=find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests')),
        package_data={},
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU Affero General Public License v3',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
        ],
        include_package_data=True,
        zip_safe=False,
        install_requires=[
            'pyserial>=3.2.1',
            'pyserial-asyncio>=0.2',
        ],
        tests_require=[
        ],
        test_suite='tests',
    )
