# Examples of plugins
This folder contains examples of plugins that can be used by applications using `wrktoolbox`.

Plugins can be used to alter the configuration of each benchmark, for example to obtain and use an access token for 
endpoints that require authentication; and to configure custom persistence layers for benchmarks results.

## Using plugins
Plugins must be specified in the settings file, and get imported dynamically from a path relative to the current working directory.

YAML example:
```yaml
plugins:
  - plugins.plugin1
  - plugins.plugin2
```

JSON example:
```json
{
    "plugins": ["plugins.plugin1", "plugins.plugin2"]
}
```

## Custom store
The file `plugin1.py` contains an example of custom store definition. Custom store types must be subclasses of 
`wrktoolbox.benchmarks.BenchmarkOutputStore`.

```python
# in this example, a plugin is used to register a new type of store
from wrktoolbox.wrkoutput import BenchmarkOutput
from wrktoolbox.benchmarks import BenchmarkSuite, BenchmarkOutputStore, BenchmarkConfig


class FooOutputStore(BenchmarkOutputStore):

    type_name = 'foo'
    
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def store(self, config: BenchmarkConfig, output: BenchmarkOutput):
        """implement here your method to store data"""
        
    def store_suite(self, suite: BenchmarkSuite):
        pass
```

Custom store types registered in plugins, can then be configured as valid stores in the settings file.
If custom stores need input to their constructors, specify settings with matching names using the notation described below.

YAML example: 
```yaml

stores:
  - type: foo
    connection_string: YOUR_CONNECTION_STRING 
```

JSON example:
```json
{
    "stores": {
      "type": "foo",
      "connection_string": "YOUR_CONNECTION_STRING"
    }
}
```

# Setup functions
Plugins can be used to alter the configuration of each benchmark. To do so, define a function called `setup`, handling two input
parameters: the first one is the instance of `BenchmarkSuite`; the second is the configured logger for the CLI.
If desired, this function can also be used to modify the logger configuration.

```python
from logging import Logger
from wrktoolbox.benchmarks import BenchmarkSuite


# in this example, a plugin is used to alter the configuration of each benchmark
def setup(suite: BenchmarkSuite, logger: Logger):

    logger.info('Obtaining an access token for benchmarks')

    # example: obtain an access token for your service
    access_token = 'example!'

    for configuration in suite.configurations:
        if not configuration.headers:
            configuration.headers = {}

        configuration.headers['Authorization'] = f'Bearer {access_token}'
```