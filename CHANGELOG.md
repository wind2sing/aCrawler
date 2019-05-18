# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [0.0.3](https://github.com/pansenlin30/aCrawler/compare/v0.0.2...v0.0.3) (2019-05-18)


### Bug Fixes

* **examples:** update due to breaking change ([1839f95](https://github.com/pansenlin30/aCrawler/commit/1839f95))
* **global:** not contain self.logger anymore ([0691204](https://github.com/pansenlin30/aCrawler/commit/0691204))
* **http:** correct request's encoding ([64129a2](https://github.com/pansenlin30/aCrawler/commit/64129a2))
* **http:** detach Response from aiohttp.ClientResponse ([3b168d3](https://github.com/pansenlin30/aCrawler/commit/3b168d3))
* **http:** Request/Response now only accept one callback function ([2e7171b](https://github.com/pansenlin30/aCrawler/commit/2e7171b))
* **http:** Response dynamically decode body & slim codes ([c782e5c](https://github.com/pansenlin30/aCrawler/commit/c782e5c))
* **http:** use aiofiles to write files ([7f22025](https://github.com/pansenlin30/aCrawler/commit/7f22025))


### Features

* **examples:** crawl v2ex hot page ([314c3a7](https://github.com/pansenlin30/aCrawler/commit/314c3a7))
* allow to directly yield dictionary & no pyquery ([9c9d3bd](https://github.com/pansenlin30/aCrawler/commit/9c9d3bd))
* **examples:** provide Redis-based quotes crawler ([39357bd](https://github.com/pansenlin30/aCrawler/commit/39357bd))
* **examples:** provide WALLHAVEN downloader ([a40b9e5](https://github.com/pansenlin30/aCrawler/commit/a40b9e5))
* **handlers:** check Response' status < 400 ([8743537](https://github.com/pansenlin30/aCrawler/commit/8743537))
* **http:** add pickle support for Request class ([a4c98de](https://github.com/pansenlin30/aCrawler/commit/a4c98de))
* **http:** implement FileRequest to download/save file ([e034360](https://github.com/pansenlin30/aCrawler/commit/e034360))
* **http:** use List to store multiple callback functions ([1a753ac](https://github.com/pansenlin30/aCrawler/commit/1a753ac))
* **middleware:** multiple families for Task and only one for Handler ([878d89d](https://github.com/pansenlin30/aCrawler/commit/878d89d))
* **middleware:** use decorator to append Handler ([20453cd](https://github.com/pansenlin30/aCrawler/commit/20453cd)), closes [#1](https://github.com/pansenlin30/aCrawler/issues/1)
* **parse:** implement Response.urljoin ([22329d2](https://github.com/pansenlin30/aCrawler/commit/22329d2))
* **parse:** support callback() decorator ([19fe8c4](https://github.com/pansenlin30/aCrawler/commit/19fe8c4))
* **utils:** better support for aioredis ([9920405](https://github.com/pansenlin30/aCrawler/commit/9920405))


### Tests

* AsyncPQ & RedisPQ ([1183892](https://github.com/pansenlin30/aCrawler/commit/1183892))


### BREAKING CHANGES

* **middleware:** other method to add Handler is not recommended. user @middleware.register(,,)
instead.
* **global:** Now all classes don't contain logger member. You can use acrawler.get_logger() to
get a logger.



### 0.0.2 (2019-05-15)


### Bug Fixes

* **item:** change rule naming to rules ([3173077](https://github.com/pansenlin30/aCrawler/commit/3173077))
* **item:** support custom parsel's parse ([c0714eb](https://github.com/pansenlin30/aCrawler/commit/c0714eb))
* dynamically import aioredis ([7071ba4](https://github.com/pansenlin30/aCrawler/commit/7071ba4))


### Features

* **http:** add sel / callback to response; add url_str & logger ([84a412b](https://github.com/pansenlin30/aCrawler/commit/84a412b))
* **middleware:** handlers support priority ([f1106b2](https://github.com/pansenlin30/aCrawler/commit/f1106b2))


### Tests

* request and fingerprint ([d8112e2](https://github.com/pansenlin30/aCrawler/commit/d8112e2))
