from setuptools import setup, find_packages


NAME = "acrawler"
DESCRIPTION = "A simple web-crawling framework, based on aiohttp."
URL = "https://github.com/wooddance/aCrawler"
EMAIL = "zireael.me@gmail.com"
AUTHOR = "wooddance"
VERSION = "0.1.3"
REQUIRED = ["aiohttp", "parsel", "cchardet"]

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=open("README.rst").read(),
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    python_requires=">=3.6.0",
    install_requires=REQUIRED,
    packages=["acrawler"],
)
