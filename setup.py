from setuptools import setup


NAME = 'acrawler'
DESCRIPTION = 'A simple web-crawling framework, based on aiohttp.'
URL = 'https://github.com/pansenlin30/aCrawler'
EMAIL = 'zireael.me@gmail.com'
AUTHOR = 'wooddance'
VERSION = '0.0.8'

packages = ['acrawler']
requires = [
    'aiohttp',
    'aiofiles',
    'parsel',
    'pyquery',
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
)
