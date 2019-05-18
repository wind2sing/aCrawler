from setuptools import setup


NAME = 'acrawler'
DESCRIPTION = 'A simple web-crawling framework, based on aiohttp.'
URL = 'https://github.com/pansenlin30/aCrawler'
EMAIL = 'zireael.me@gmail.com'
AUTHOR = 'Pan Senlin'
VERSION = '0.0.3'

packages = ['acrawler']
requires = [
    'aiohttp',
    'aiofiles',
    'pyquery',
    'uvloop',
    'parsel',
    'cchardet'
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
