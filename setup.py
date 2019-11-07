from setuptools import setup


NAME = "acrawler"
DESCRIPTION = "A simple web-crawling framework, based on aiohttp."
URL = "https://github.com/wooddance/aCrawler"
EMAIL = "zireael.me@gmail.com"
AUTHOR = "wooddance"
VERSION = "0.1.5"
REQUIRED = ["aiohttp", "parsel", "cchardet", "dill"]

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
