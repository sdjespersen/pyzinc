from setuptools import setup

setup(
    name='pyzinc',
    url='https://github.com/sdjespersen/pyzinc',
    description='Parser for Project Haystack Zinc file format',
    version='0.0.1',
    author='Scott Jespersen',
    license='BSD',
    packages=[
        'pyzinc',
    ],
    requires=[
        'pandas',
    ],
)
