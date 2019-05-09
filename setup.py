from setuptools import setup


NAME = 'acrawler'
DESCRIPTION = ''
URL = ''
EMAIL = 'zireael.me@gmail.com'
AUTHOR = 'Pan Senlin'
VERSION = '0.0.1'

packages = ['acrawler']
requires = [
    'aiohttp',
    'pyquery',
    'uvloop',
    'parsel'
]
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    python_requires='>=3.6.0',
    packages=packages,
    install_requires=requires,
    license='MIT',
)
