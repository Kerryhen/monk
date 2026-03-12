# Changelog

## [0.2.0](https://github.com/Kerryhen/monk/compare/monk-api-v0.1.1...monk-api-v0.2.0) (2026-03-12)


### Features

* **api:** add /v1 URL prefix and release automation ([ea1a2e7](https://github.com/Kerryhen/monk/commit/ea1a2e711e1a5828cb80d904554dc1685fbb4a31))
* **api:** implement campaign management with client ownership ([0e0ca16](https://github.com/Kerryhen/monk/commit/0e0ca16f3a3aa1bfefc522c78a9de0b4e840e08c))
* **api:** migrate client identifier from query param to X-Instance-ID header ([1560d33](https://github.com/Kerryhen/monk/commit/1560d337ef02488b5756a757ad759e8313a4e176))
* **messenger:** add messenger gateway with pluggable handler registry ([7dfe104](https://github.com/Kerryhen/monk/commit/7dfe1047f0f82379ff0449205e2540846ff553a3))
* **observability:** add structured logging across interface and sessions ([06b21f7](https://github.com/Kerryhen/monk/commit/06b21f799d8880f90dde32d8d44f338da04bee4b))
* **subscribers:** add JSON import endpoint ([12fc58a](https://github.com/Kerryhen/monk/commit/12fc58a70fe031e267151dbd0bce328fa86bb247))
* **subscribers:** add JSON import endpoint ([12fc58a](https://github.com/Kerryhen/monk/commit/12fc58a70fe031e267151dbd0bce328fa86bb247))
* **subscribers:** add JSON import endpoint with list ownership fallback ([8470d5e](https://github.com/Kerryhen/monk/commit/8470d5e9e0cb64aa71ad1d2f08013d6a6555a0ac))
* **subscribers:** implement CSV import endpoint with default list tracking ([5420944](https://github.com/Kerryhen/monk/commit/542094451358891eb717aa06800d9877b962baed))
* **tests:** add campaign start/stop tests and fake handler capture ([fea3c50](https://github.com/Kerryhen/monk/commit/fea3c50d3626ef1266567686a4907ca88af0e85d))


### Bug Fixes

* **campaigns:** enforce ownership on list updates and add missing auth tests ([43aa56d](https://github.com/Kerryhen/monk/commit/43aa56de17a2b6f75b05cafbca496170dba7b296))
* **subscribers:** enforce list ownership on import and add cleanup ([9f86adc](https://github.com/Kerryhen/monk/commit/9f86adc4de8187e83be5df28c0e11a30409a6693))


### Documentation

* **messenger:** add handler guide with integration example ([3f61280](https://github.com/Kerryhen/monk/commit/3f612805c079535b918d64e1ef08e39c727a83cb))
* **observability:** add logging guide with OTel migration path ([183018f](https://github.com/Kerryhen/monk/commit/183018ff12741d23c850579ecb7638e9185d4679))
