# Python script to query REST-API from empirica-systeme, see https://www.empirica-systeme.de/en/portfolio/empirica-systeme-rest-api/
# This work is licensed under a "Creative Commons Attribution 4.0 International License", sett http://creativecommons.org/licenses/by/4.0/
# Documentation of REST-API at https://api.empirica-systeme.de/api-docs/

#!/usr/bin/env python3
from setuptools import find_packages, setup

install_requires = [
    'requests',
]

tests_requires=[
    'pytest',
    'pytest-cov',
]

setup(
    name='analystApi',
    version='0.0.2',
    #license='MIT',
    author='empirica-systeme',
    author_email='info@empirica-systeme.de',
    description='',
    # long_description=readme,
    packages=['analystApi',],
    zip_safe=True,
    platforms='any',
    install_requires=install_requires,
    tests_requires=tests_requires,
    entry_points={
         'console_scripts': [
             'analystApi_csv = analystApi.csv_transform:main',
         ],
     },
)
