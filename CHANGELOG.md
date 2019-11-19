# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [0.1.6](https://github.com/wooddance/aCrawler/compare/v0.1.5...v0.1.6) (2019-11-18)


### Bug Fixes

* **counter:** init config after load ([656c5a7](https://github.com/wooddance/aCrawler/commit/656c5a7))
* **crawler:** meta merge ([07af099](https://github.com/wooddance/aCrawler/commit/07af099))
* **item:** family argument ([85a9ff6](https://github.com/wooddance/aCrawler/commit/85a9ff6))


### Features

* **chain:** default & kwargs ([8629dcf](https://github.com/wooddance/aCrawler/commit/8629dcf))
* **item:** meta considered as xpath vars ([a34750b](https://github.com/wooddance/aCrawler/commit/a34750b))
* **item:** ParselxItem ([a3ef679](https://github.com/wooddance/aCrawler/commit/a3ef679))
* **task:** pass meta between parent and child task ([3ae6c46](https://github.com/wooddance/aCrawler/commit/3ae6c46))



### [0.1.5](https://github.com/wooddance/aCrawler/compare/v0.1.4...v0.1.5) (2019-11-07)


### Bug Fixes

* **chain:** change naming ([62995e2](https://github.com/wooddance/aCrawler/commit/62995e2))
* **chain:** spawn crawler during run() ([6ccee3a](https://github.com/wooddance/aCrawler/commit/6ccee3a))
* **cralwer:** wrong default values ([2ec846f](https://github.com/wooddance/aCrawler/commit/2ec846f))
* **examples:** custom process change ([b926c78](https://github.com/wooddance/aCrawler/commit/b926c78))
* **exceptions:** dumping error ([4157c3b](https://github.com/wooddance/aCrawler/commit/4157c3b))
* **http:** default callback condition check ([0d40b67](https://github.com/wooddance/aCrawler/commit/0d40b67))
* **http:** FileRequest filename ([76bc483](https://github.com/wooddance/aCrawler/commit/76bc483))
* **http:** pass meta args ([6c2b64b](https://github.com/wooddance/aCrawler/commit/6c2b64b))
* **item:** log as class attr ([66222c1](https://github.com/wooddance/aCrawler/commit/66222c1))
* **item:** log, store as attributes ([12d5a33](https://github.com/wooddance/aCrawler/commit/12d5a33))
* **log:** remove handlers at beginning ([a143405](https://github.com/wooddance/aCrawler/commit/a143405))
* **middleware:** change default priority; add name ([e5f1573](https://github.com/wooddance/aCrawler/commit/e5f1573))
* **middleware:** check if the handler already exists ([69e6c1e](https://github.com/wooddance/aCrawler/commit/69e6c1e))
* **web:** change naming; expose routes; ([c077f01](https://github.com/wooddance/aCrawler/commit/c077f01))
* **web:** default action return items ([6981883](https://github.com/wooddance/aCrawler/commit/6981883))
* default values; naming; ([dee18c5](https://github.com/wooddance/aCrawler/commit/dee18c5))


### Features

* **acrawler:** add_and_wait ([256cbb4](https://github.com/wooddance/aCrawler/commit/256cbb4))
* **chain:** add multiple tasks ([0b6d14a](https://github.com/wooddance/aCrawler/commit/0b6d14a))
* **chain:** ChainCrawler use(); typo ([71dbf2d](https://github.com/wooddance/aCrawler/commit/71dbf2d))
* **chain:** implement ChainCrawler ChainRequest ([0d59537](https://github.com/wooddance/aCrawler/commit/0d59537))
* **chain:** implement ChainItem ([9807b9c](https://github.com/wooddance/aCrawler/commit/9807b9c))
* **chain:** pretty debug ([b7f3995](https://github.com/wooddance/aCrawler/commit/b7f3995))
* **chain:** spawn by xpath rule ([4bb2271](https://github.com/wooddance/aCrawler/commit/4bb2271))
* **chain:** status control ([6e2c8f6](https://github.com/wooddance/aCrawler/commit/6e2c8f6))
* **chain:** support web service ([b9f7c32](https://github.com/wooddance/aCrawler/commit/b9f7c32))
* **expiredwathcer:** delay and retry ([fd1f135](https://github.com/wooddance/aCrawler/commit/fd1f135))
* **http:** FileRequest use args to determine fdir ([f0aff89](https://github.com/wooddance/aCrawler/commit/f0aff89))
* **middleware:** [@register](https://github.com/register) accepts more types ([dbf28ad](https://github.com/wooddance/aCrawler/commit/dbf28ad))
* **middleware:** [@register](https://github.com/register) supports generator func ([f83b11d](https://github.com/wooddance/aCrawler/commit/f83b11d))
* **parser:** accepts callbacks ([4ea5b8e](https://github.com/wooddance/aCrawler/commit/4ea5b8e))
* **processors:** processors of string type ([31fa2c3](https://github.com/wooddance/aCrawler/commit/31fa2c3))
* **processors:** re_groups ([157e481](https://github.com/wooddance/aCrawler/commit/157e481))
* **processors:** register&use ([e46b7b7](https://github.com/wooddance/aCrawler/commit/e46b7b7))
* **processors:** support drop_item ([44efee0](https://github.com/wooddance/aCrawler/commit/44efee0))
* **processors:** to_date enhanced ([9c1fa22](https://github.com/wooddance/aCrawler/commit/9c1fa22))
* **web:** expose web.routes ([94a8c30](https://github.com/wooddance/aCrawler/commit/94a8c30))
* **x:** processors as a module ([7032286](https://github.com/wooddance/aCrawler/commit/7032286))



### [0.1.4](https://github.com/wooddance/aCrawler/compare/v0.1.3...v0.1.4) (2019-09-17)


### Bug Fixes

* **crawler:** remove signal handlers after shutdown ([2cf1bff](https://github.com/wooddance/aCrawler/commit/2cf1bff))
* **handlers:** ToMongo won't create index ([73cc390](https://github.com/wooddance/aCrawler/commit/73cc390))
* **log:** change logger formatter ([30e5068](https://github.com/wooddance/aCrawler/commit/30e5068))


### Features

* **cralwer:** middleware with priority True ([b30f836](https://github.com/wooddance/aCrawler/commit/b30f836))
* **crawler:** use dill for pickling ([b3228ad](https://github.com/wooddance/aCrawler/commit/b3228ad))
* **response:** paginate accepts keyword arguments ([fcd59cc](https://github.com/wooddance/aCrawler/commit/fcd59cc))



### [0.1.3](https://github.com/wooddance/aCrawler/compare/v0.1.1...v0.1.3) (2019-08-24)


### Tests

* queue ([a0a436e](https://github.com/wooddance/aCrawler/commit/a0a436e))
* request ([5dc44a4](https://github.com/wooddance/aCrawler/commit/5dc44a4))
* scheduler ([bdec6d2](https://github.com/wooddance/aCrawler/commit/bdec6d2))



### [0.1.1](https://github.com/wooddance/aCrawler/compare/v0.1.0...v0.1.1) (2019-08-23)


### Bug Fixes

* style ([9f91351](https://github.com/wooddance/aCrawler/commit/9f91351))



## [0.1.0](https://github.com/wooddance/aCrawler/compare/v0.0.9...v0.1.0) (2019-08-23)


### Bug Fixes

* **examples:** update for change of item parsing rules ([4eea6ac](https://github.com/wooddance/aCrawler/commit/4eea6ac))
* **handler:** event as instance'attr ([6d3164d](https://github.com/wooddance/aCrawler/commit/6d3164d))
* **item:** clean processors ([a90470a](https://github.com/wooddance/aCrawler/commit/a90470a))
* **item:** clean rules ([fe48ef8](https://github.com/wooddance/aCrawler/commit/fe48ef8))
* **task:** optional ancestor ([0a2df10](https://github.com/wooddance/aCrawler/commit/0a2df10))


### Features

* **counter:** accept flag param ([adfeb10](https://github.com/wooddance/aCrawler/commit/adfeb10))
* **counter:** count requests in progress ([3ae9753](https://github.com/wooddance/aCrawler/commit/3ae9753))
* **counter:** delay in counter ([cd734ec](https://github.com/wooddance/aCrawler/commit/cd734ec))
* **crawler:** check import ([ab300b2](https://github.com/wooddance/aCrawler/commit/ab300b2))
* **crawler:** name attr ([35d62a2](https://github.com/wooddance/aCrawler/commit/35d62a2))
* **crawler:** pickle all types of task ([53e087f](https://github.com/wooddance/aCrawler/commit/53e087f))
* **http:** picklable response ([93c74de](https://github.com/wooddance/aCrawler/commit/93c74de))
* **item:** picklable ([fc16e41](https://github.com/wooddance/aCrawler/commit/fc16e41))
* **item:** support dropField ([49f1d2c](https://github.com/wooddance/aCrawler/commit/49f1d2c))
* **item:** support inline rule ([e864a4a](https://github.com/wooddance/aCrawler/commit/e864a4a))
* **response:** paginate & follow ([c66d0d3](https://github.com/wooddance/aCrawler/commit/c66d0d3))



### [0.0.9](https://github.com/wooddance/aCrawler/compare/v0.0.8...v0.0.9) (2019-07-28)


### Bug Fixes

* max_requests & download_delay bug ([0681ad9](https://github.com/wooddance/aCrawler/commit/0681ad9))
* **http:** correct fingerprint for request ([ba2aba1](https://github.com/wooddance/aCrawler/commit/ba2aba1))
* **utils:** make_links_absolute fix dot_all ([c5ff219](https://github.com/wooddance/aCrawler/commit/c5ff219))
* bugs ([459bef3](https://github.com/wooddance/aCrawler/commit/459bef3))
* **exceptions:** reschedule now release req limit ([c648215](https://github.com/wooddance/aCrawler/commit/c648215))
* **http:** req hosts limits ([ec4593d](https://github.com/wooddance/aCrawler/commit/ec4593d))
* **item:** default processor strip ([7562bb8](https://github.com/wooddance/aCrawler/commit/7562bb8))


### Features

* **handlers:** implement ExpiredWatcher ([3cb2e8d](https://github.com/wooddance/aCrawler/commit/3cb2e8d))
* **http:** open method for response ([659544a](https://github.com/wooddance/aCrawler/commit/659544a))
* **item:** add bind meth for processors ([61bc0fa](https://github.com/wooddance/aCrawler/commit/61bc0fa))
* **item:** add store attr ([023b796](https://github.com/wooddance/aCrawler/commit/023b796))
* **item:** new Field parsing ([501164f](https://github.com/wooddance/aCrawler/commit/501164f))
* **item:** processors map & filter ([969762d](https://github.com/wooddance/aCrawler/commit/969762d))
* **utils:** sync_coroutine ([80853bb](https://github.com/wooddance/aCrawler/commit/80853bb))



### [0.0.8](https://github.com/wooddance/aCrawler/compare/v0.0.7...v0.0.8) (2019-07-02)


### Bug Fixes

* **crawler:** add dict new_task ([039ff93](https://github.com/wooddance/aCrawler/commit/039ff93))
* **crawler:** simplify logging ([c5bf20a](https://github.com/wooddance/aCrawler/commit/c5bf20a))
* **examples:** update wh-crawler for new site ([cdfafe3](https://github.com/wooddance/aCrawler/commit/cdfafe3))
* **handlers:** tomongo supports index ([d0051c1](https://github.com/wooddance/aCrawler/commit/d0051c1))
* **http:** BrowserRequest's exception catching ([5049a3e](https://github.com/wooddance/aCrawler/commit/5049a3e))
* **http:** correct absolut links ([ed66892](https://github.com/wooddance/aCrawler/commit/ed66892))
* **http:** not catching json error anymore ([06086a1](https://github.com/wooddance/aCrawler/commit/06086a1))
* **scheduler:** transfer waiting queue using zrangebyscore ([af3574d](https://github.com/wooddance/aCrawler/commit/af3574d))


### Features

* **crawler:** now task can be yielded from handler ([b235261](https://github.com/wooddance/aCrawler/commit/b235261))
* **examples:** crawl pythonclock.org (javascript) ([17334ca](https://github.com/wooddance/aCrawler/commit/17334ca))
* **http:** add PyQuery support ([4137cbf](https://github.com/wooddance/aCrawler/commit/4137cbf))
* **http:** implement BrowserRequest ([58aa947](https://github.com/wooddance/aCrawler/commit/58aa947)), closes [#9](https://github.com/wooddance/aCrawler/issues/9)
* **http:** special delay and random delay ([76eae8f](https://github.com/wooddance/aCrawler/commit/76eae8f))
* **http:** support absolute links ([d34f08e](https://github.com/wooddance/aCrawler/commit/d34f08e))
* **http:** support DISABLE_COOKIES ([0123526](https://github.com/wooddance/aCrawler/commit/0123526))
* **parser:** support add_meta ([dca8505](https://github.com/wooddance/aCrawler/commit/dca8505))
* **web:** implement web_action_after_query ([2481e8d](https://github.com/wooddance/aCrawler/commit/2481e8d))



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
