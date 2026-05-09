"""Package setup for rlai_utils."""

import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'rlai_utils'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Robolabs AI',
    maintainer_email='contact@robolabs.ai',
    description='Diagnostics, benchmarks, and RViz helpers for rbot',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [],
    },
)
