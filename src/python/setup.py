__author__ = 'tom'

from setuptools import setup, find_namespace_packages

setup(
    name='approxeng.util',
    version='0.1.0',
    description='Utility library used by other approxeng.* libraries',
    classifiers=['Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.8',
                 'Programming Language :: Python :: 3.9',
                 'Programming Language :: Python :: 3.10',
                 'License :: OSI Approved :: MIT License'],
    url='https://github.com/approxeng/approxeng.util/',
    author='Tom Oinn',
    author_email='tomoinn@gmail.com',
    license='MIT',
    packages=find_namespace_packages(),
    install_requires=[],
    package_data={},
    dependency_links=[],
    entry_points={
        'console_scripts': []
    },
    zip_safe=False)
