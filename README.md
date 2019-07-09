[![Build status](https://dev.azure.com/robertoprevato/wrktoolbox/_apis/build/status/wrktoolbox-CI)](https://dev.azure.com/robertoprevato/wrktoolbox/_build/latest?definitionId=19) [![pypi](https://img.shields.io/pypi/v/wrktools.svg?color=blue)](https://pypi.org/project/wrktools/) [![Test coverage](https://img.shields.io/azure-devops/coverage/robertoprevato/wrktoolbox/19.svg)](https://robertoprevato.visualstudio.com/wrktoolbox/_build?definitionId=19)

# wrktoolbox
A tool to run wrk and wrk2 benchmarks, store their output, and generate reports.

## Features
* Support for YAML and JSON configuration files, to define benchmark suites
* Parses the output of [wrk](https://github.com/wg/wrk) and [wrk2](https://github.com/giltene/wrk2) HTTP benchmarking tools
* Possibility to define performance goals, which are evaluated and stored with results
* Strategy to store benchmarks results and whole suite configuration
* Support for [plugins](https://github.com/RobertoPrevato/wrktoolbox/wiki/Plugins), loaded dynamically to define new types of stores, performance goals, and reports writers
* Strategy to produce reports of results, for example [to XLSX, with wrktoolbox-xlsx](https://github.com/RobertoPrevato/wrktoolbox-xlsx) - see [Wiki](https://github.com/RobertoPrevato/wrktoolbox/wiki/Reports)
* [Docker images for Ubuntu and Alpine](https://github.com/RobertoPrevato/wrktoolbox/tree/master/docker)
* [CLI](https://github.com/RobertoPrevato/wrktoolbox/wiki/CLI)

## Quick example

1. install

```bash
pip install wrktools
```

2. verify that the cli works (optional)

```bash
wrktoolbox --help
```

3. prepare a YAML, or JSON file with configuration.
A basic example, with a single type of benchmark, looks like this:

```yaml
# the array of benchmarks contains the configuration of benchmarks to run
benchmarks:
  - url: https://this-is-an-example.it/api/alive
    threads: 10  # threads count
    concurrency: 100  # concurrent users
    duration: 30  # test duration in seconds

# the type of stores to use, to collect benchmark results
# it is possible to define custom stores, using plugins;
# for example to store results in a database, or send them to an API
stores:
  - json
```

4. run a suite of benchmarks using a settings file

```bash
wrktoolbox run --settings basic.yaml
```

Refer to examples folder for an example of full configuration file, defining plugins for authentication and custom store.
