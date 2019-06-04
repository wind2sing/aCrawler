# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [0.0.7](https://github.com/pansenlin30/aCrawler/compare/v0.0.6...v0.0.7) (2019-06-04)


### Bug Fixes

* **crawler:** cancel task correctly ([803160f](https://github.com/pansenlin30/aCrawler/commit/803160f))
* **crawler:** crawler's method can be pickled now ([480b8f0](https://github.com/pansenlin30/aCrawler/commit/480b8f0))
* **crawler:** dynamically configure & style fix ([03d975f](https://github.com/pansenlin30/aCrawler/commit/03d975f))
* **crawler:** enable attributes are properties now ([b8d67c0](https://github.com/pansenlin30/aCrawler/commit/b8d67c0))
* **crawler:** import user setting ([8630714](https://github.com/pansenlin30/aCrawler/commit/8630714))
* **crawler:** shutdown correctly to wait for nonrequest and nonwaiting tasks ([badf859](https://github.com/pansenlin30/aCrawler/commit/badf859))
* **crawler:** start_requests() supports NonRequest Task ([cbc5271](https://github.com/pansenlin30/aCrawler/commit/cbc5271))
* **crawler:** start,finish are methods now ([5872fc4](https://github.com/pansenlin30/aCrawler/commit/5872fc4))
* **handler:** check before add callbacks to response ([0c4061f](https://github.com/pansenlin30/aCrawler/commit/0c4061f))
* **http:** initialize Response directly ([bc6aafc](https://github.com/pansenlin30/aCrawler/commit/bc6aafc))
* **setting:** clear relations of config redis/web/lock ([aaae1d9](https://github.com/pansenlin30/aCrawler/commit/aaae1d9))
* **task:** better retry/recrawl & ignore_exception ([cd4ff49](https://github.com/pansenlin30/aCrawler/commit/cd4ff49))
* **task:** default fingerprint is __hash__() ([b53e6d4](https://github.com/pansenlin30/aCrawler/commit/b53e6d4))


### Features

* **counter:** enable persistence ([ed1fbbe](https://github.com/pansenlin30/aCrawler/commit/ed1fbbe))
* **counter:** implement counter in diff module ([7f11017](https://github.com/pansenlin30/aCrawler/commit/7f11017))
* **counter:** implement Redis Counter ([2a8d9ba](https://github.com/pansenlin30/aCrawler/commit/2a8d9ba))
* **counter:** support join_by_ancestor ([e59587c](https://github.com/pansenlin30/aCrawler/commit/e59587c))
* **crawler:** support customed web_add_task_query() ([926d411](https://github.com/pansenlin30/aCrawler/commit/926d411))
* **crawler:** support LOCK_ALWAYS without Counter ([3acb588](https://github.com/pansenlin30/aCrawler/commit/3acb588))
* **crawler:** support ReScheduleError ([b797272](https://github.com/pansenlin30/aCrawler/commit/b797272))
* **crawler:** support web service (add_task) ([0face33](https://github.com/pansenlin30/aCrawler/commit/0face33))
* **http:** response now has property: json ([8da841c](https://github.com/pansenlin30/aCrawler/commit/8da841c))
* **http:** support MAX_REQUESTS_PER_HOST ([23dbc85](https://github.com/pansenlin30/aCrawler/commit/23dbc85))
* **http:** support MAX_REQUESTS_PER_HOST / SPECIAL_HOST using Counter ([feb7139](https://github.com/pansenlin30/aCrawler/commit/feb7139))
* **task:** support ignore_exception and exceptions ([1a188b0](https://github.com/pansenlin30/aCrawler/commit/1a188b0))
* **task:** support SkipTaskError ([0edcb87](https://github.com/pansenlin30/aCrawler/commit/0edcb87))


### refactor

* **settings:** max_requests not accepted as Crawler's attribute ([dc36db9](https://github.com/pansenlin30/aCrawler/commit/dc36db9))


### Tests

* two errors ([ac47cc1](https://github.com/pansenlin30/aCrawler/commit/ac47cc1))


### BREAKING CHANGES

* **settings:** You must use config to assign MAX_REQUESTS



### [0.0.6](https://github.com/pansenlin30/aCrawler/compare/v0.0.5...v0.0.6) (2019-05-27)


### Bug Fixes

* **crawler:** correct pickling methods ([11dfa0c](https://github.com/pansenlin30/aCrawler/commit/11dfa0c))
* **http:** provide your encoding ([e7ad7f2](https://github.com/pansenlin30/aCrawler/commit/e7ad7f2))


### Features

* **examples:** imdb popular movies ([1791d82](https://github.com/pansenlin30/aCrawler/commit/1791d82))
* **handlers:** ItemToMongo supports update operation ([557c0b5](https://github.com/pansenlin30/aCrawler/commit/557c0b5))
* **item:** ParselItem supports default processors (strip by default) ([0826548](https://github.com/pansenlin30/aCrawler/commit/0826548))
* **parse:** urljoin now also accepts list ([463ab93](https://github.com/pansenlin30/aCrawler/commit/463ab93))



### [0.0.5](https://github.com/pansenlin30/aCrawler/compare/v0.0.4...v0.0.5) (2019-05-21)


### Bug Fixes

* **crawler:** use parsers rather than Parsers ([b01ffdc](https://github.com/pansenlin30/aCrawler/commit/b01ffdc))
* **item:** better log & not support custom_parse ([1db20b7](https://github.com/pansenlin30/aCrawler/commit/1db20b7))


### Features

* **examples:** scrape Bilibili video info ([e81d5d2](https://github.com/pansenlin30/aCrawler/commit/e81d5d2))
* **parse:** Request from start_request() has default callback parse() ([9c061fc](https://github.com/pansenlin30/aCrawler/commit/9c061fc))



### [0.0.5](https://github.com/pansenlin30/aCrawler/compare/v0.0.4...v0.0.5) (2019-05-21)


### Bug Fixes

* **crawler:** use parsers rather than Parsers ([b01ffdc](https://github.com/pansenlin30/aCrawler/commit/b01ffdc))
* **item:** better log & not support custom_parse ([1db20b7](https://github.com/pansenlin30/aCrawler/commit/1db20b7))


### Features

* **examples:** scrape Bilibili video info ([e81d5d2](https://github.com/pansenlin30/aCrawler/commit/e81d5d2))
* **parse:** Request from start_request() has default callback parse() ([9c061fc](https://github.com/pansenlin30/aCrawler/commit/9c061fc))



### [0.0.5](https://github.com/pansenlin30/aCrawler/compare/v0.0.4...v0.0.5) (2019-05-21)


### Bug Fixes

* **crawler:** use parsers rather than Parsers ([b01ffdc](https://github.com/pansenlin30/aCrawler/commit/b01ffdc))
* **item:** better log & not support custom_parse ([1db20b7](https://github.com/pansenlin30/aCrawler/commit/1db20b7))


### Features

* **examples:** scrape Bilibili video info ([e81d5d2](https://github.com/pansenlin30/aCrawler/commit/e81d5d2))
* **parse:** Request from start_request() has default callback parse() ([9c061fc](https://github.com/pansenlin30/aCrawler/commit/9c061fc))



### [0.0.4](https://github.com/pansenlin30/aCrawler/compare/v0.0.3...v0.0.4) (2019-05-20)


### Bug Fixes

* **crawler:** shutdown after non-request tasks finish ([dc5404c](https://github.com/pansenlin30/aCrawler/commit/dc5404c))
* **examples:** update WALLHAVEN with callback ([93c6dae](https://github.com/pansenlin30/aCrawler/commit/93c6dae))
* **http:** fix pickle for Request ([6b83d36](https://github.com/pansenlin30/aCrawler/commit/6b83d36))


### Features

* **crawler:** catch system's signals gracefully ([f5f595c](https://github.com/pansenlin30/aCrawler/commit/f5f595c)), closes [#3](https://github.com/pansenlin30/aCrawler/issues/3)
* **crawler:** support persistent crawling ([d55cfce](https://github.com/pansenlin30/aCrawler/commit/d55cfce)), closes [#4](https://github.com/pansenlin30/aCrawler/issues/4)
* **handler:** support mongodb & fix bugs ([8956a31](https://github.com/pansenlin30/aCrawler/commit/8956a31))
* **http:** support status_allowed parameter and setting ([dc86fdf](https://github.com/pansenlin30/aCrawler/commit/dc86fdf))
* **item:** custom_process allows async/asyncgenerator ([3a6f64b](https://github.com/pansenlin30/aCrawler/commit/3a6f64b))
* **parse:** ParselItem supports rules_first ([e6cd5c3](https://github.com/pansenlin30/aCrawler/commit/e6cd5c3))
* **task:** support recrawl, exetime ([77c59d7](https://github.com/pansenlin30/aCrawler/commit/77c59d7)), closes [#5](https://github.com/pansenlin30/aCrawler/issues/5)



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
