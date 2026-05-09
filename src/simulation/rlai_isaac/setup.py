"""Package setup for rlai_isaac."""

from setuptools import find_packages, setup

package_name = 'rlai_isaac'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Robolabs AI',
    maintainer_email='contact@robolabs.ai',
    description='NVIDIA Isaac Sim 5.0 integration for rbot',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [],
    },
)
