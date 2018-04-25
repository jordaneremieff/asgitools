import os
from setuptools import find_packages, setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='asgitools',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'uvicorn',
        'Werkzeug',
        'asyncio_redis',
        'asgiref',
    ],
    author='Jordan E.',
    author_email='jermff@gmail.com',
)
