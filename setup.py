from setuptools import setup


NAME = "acrawler"
DESCRIPTION = "A simple web-crawling framework, based on aiohttp."
URL = "https://github.com/wooddance/aCrawler"
EMAIL = "zireael.me@gmail.com"
AUTHOR = "wooddance"
VERSION = "0.0.9"

packages = ["acrawler"]
requires = ["aiohttp", "aiofiles", "parsel", "pyquery", "cchardet"]
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=open("README.rst").read(),
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    python_requires=">=3.6.0",
    packages=packages,
    install_requires=requires,
)
