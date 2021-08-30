#!/usr/bin/env python3

from os.path import abspath, dirname, join
import pip

from setuptools import setup, find_packages


# Besides not advised,
# https://pip.pypa.io/en/stable/user_guide/#using-pip-from-your-program
# That's the only sane way to parse requirements.txt
pip_major_version = int(pip.__version__.split(".")[0])
if pip_major_version >= 20:
    from pip._internal.network.session import PipSession
    from pip._internal.req import parse_requirements
elif pip_major_version >= 10:
    from pip._internal.download import PipSession
    from pip._internal.req import parse_requirements
else:
    from pip.download import PipSession
    from pip.req import parse_requirements

CWD = dirname(abspath(__file__))


def requires():
    reqs_file = join(CWD, 'manager-requirements.txt')
    reqs_install = parse_requirements(reqs_file, session=PipSession())

    try:
        return [str(ir.requirement) for ir in reqs_install]
    except AttributeError:
        print('attributeError')
        return [str(ir.req) for ir in reqs_install]


setup(
    name='openstack-actions-runner',
    use_scm_version={
        'local_scheme': 'dirty-tag'
    },
    setup_requires=[
        'setuptools_scm'
    ],
    description='Scality\'s tools for github action self-hosted VM management',
    url='https://https://github.com/scality/openstack-actions-runner',
    license='Apache',
    include_package_data=True,
    packages=find_packages(include=['runners_manager', 'runners_manager.*']),
    install_requires=requires(),
    entry_points={
        'console_scripts': [
            'runner-manager=runners_manager.start:start',
        ],
    }
)
