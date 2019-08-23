from setuptools import setup, find_packages


NAME = "acrawler"
DESCRIPTION = "A simple web-crawling framework, based on aiohttp."
URL = "https://github.com/wooddance/aCrawler"
EMAIL = "zireael.me@gmail.com"
AUTHOR = "wooddance"
VERSION = "0.1.0"


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=open("README.rst").read(),
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    python_requires=">=3.6.0",
    install_requires=open("requirements.txt").read().splitlines(),
    packages=find_packages(exclude=["tests", "docs"]),
)
