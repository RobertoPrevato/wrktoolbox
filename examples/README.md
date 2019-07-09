# Examples

1. install wrktoolbox

```bash
pip install wrktoolbox
```

2. verify that the cli works (optional)

```bash
wrktoolbox --version
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

4. run a suite of benchmarks using the settings file

```bash
wrktoolbox run --settings basic.yaml
```