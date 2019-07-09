import pytest
from pytest import raises
from rocore.exceptions import InvalidArgument
# noinspection PyUnresolvedReferences
from wrktoolbox import stores
from wrktoolbox.benchmarks import BenchmarkSuite, BenchmarkConfig, WrkVariant
from wrktoolbox.wrkoutput import TimeResult


@pytest.mark.parametrize('url,threads,connections,duration,timeout,app_variant,responses_per_second,expected_cmd', [
    ['https://foo.foo', 4, 100, 20, 20, WrkVariant.WRK, None,
     'wrk https://foo.foo -c 100 -t 4 -d 20 --timeout 20'],
    ['https://example.ufo', 4, 100, 20, 20, WrkVariant.WRK, None,
     'wrk https://example.ufo -c 100 -t 4 -d 20 --timeout 20'],
    ['https://foo.foo', 4, 100, 20, 20, WrkVariant.WRK2, 4,
     'wrk2 https://foo.foo -c 100 -t 4 -d 20 --timeout 20 -R4'],
])
def test_command(url, threads, connections, duration, timeout, app_variant, responses_per_second, expected_cmd):
    config = BenchmarkConfig(url, threads, connections, duration, timeout, None, app_variant, responses_per_second)
    app_variant
    cmd = config.get_cmd()
    assert expected_cmd == cmd


@pytest.mark.parametrize('url,headers,expected_cmd', [
    ['https://foo.foo', {'foo': 'foo'}, 'wrk https://foo.foo -c 10 -t 2 -d 20 --timeout 20 --latency '
                                        '-H "foo: foo"'],
    ['https://foo.foo', {'a': 'a', 'b': 'b'}, 'wrk https://foo.foo -c 10 -t 2 -d 20 --timeout 20 --latency '
                                              '-H "a: a" -H "b: b"']
])
def test_command(url, headers, expected_cmd):
    config = BenchmarkConfig(url, threads=2, headers=headers)

    cmd = config.get_cmd()
    assert expected_cmd == cmd


def test_load_plugins():

    suite = BenchmarkSuite.from_dict({
        'plugins': ['plugins.plugin1', 'plugins.plugin2'],
        'benchmarks': [
            {
                'test_id': 1,
                'url': 'https://foo.org',
                'threads': 10,
                'concurrency': 10,
                'duration': 5
            }
        ],
        'stores': ['json', 'foo']
    })

    assert suite.plugins is not None
    assert suite.plugins[0].module.__name__ == 'plugins.plugin1'
    assert suite.plugins[1].module.__name__ == 'plugins.plugin2'
    assert suite.stores[1].__class__.__name__ == 'FooOutputStore'


def test_suite_raises_for_missing_benchmarks():
    with raises(InvalidArgument):
        BenchmarkSuite.from_dict({'stores': []})


def test_suite_raises_for_missing_stores():
    with raises(InvalidArgument):
        BenchmarkSuite.from_dict({'benchmarks': []})


@pytest.mark.parametrize('value,expected_ms', [
    [TimeResult(123.56, 'ms'), 123.56],
    [TimeResult(1.22, 's'), 1220],
    [TimeResult(12.56, 's'), 12560],
    [TimeResult(12.56, 'us'), 0.01256]
])
def test_value_result_ms(value: TimeResult, expected_ms):
    assert value.ms == expected_ms


def test_benchmark_suite_can_store_metadata():
    suite = BenchmarkSuite([], [], '', None, None)
    suite.metadata = {'location': 'Japan'}

    data = suite.to_dict()
    assert 'metadata' in data
    assert data.get('metadata').get('location') == 'Japan'


def test_benchmark_suite_base_url():
    conf = {
        'base_url': 'https://cats.me',
        'configurations': [
            {
                'url': '/api/cat'
            },
            {
                'url': '$BASEURL/api/cat'
            },
            {
                'url': 'https://dogs.com/api/cat'
            },
            {

            }
        ]
    }

    BenchmarkSuite.use_base_url(conf)
    assert conf['configurations'][0]['url'] == 'https://cats.me/api/cat'
    assert conf['configurations'][1]['url'] == 'https://cats.me/api/cat'
    assert conf['configurations'][2]['url'] == 'https://dogs.com/api/cat'
    assert conf['configurations'][3]['url'] == 'https://cats.me'


@pytest.mark.parametrize('root_setting,value', [
    ['threads', 2],
    ['concurrency', 10],
    ['responses_per_second', 10]
])
def test_benchmark_suite_root_settings(root_setting, value):
    conf = {
        root_setting: value,
        'configurations': [
            {

            },
            {
                root_setting: '$'
            },
            {

            }
        ]
    }

    BenchmarkSuite.use_root_settings(conf)
    assert conf['configurations'][0][root_setting] == value
    assert conf['configurations'][1][root_setting] == '$'
    assert conf['configurations'][2][root_setting] == value
