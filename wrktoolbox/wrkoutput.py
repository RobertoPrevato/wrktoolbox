from uuid import uuid4
from datetime import datetime
from typing import Optional, Union
from pyparsing import Literal, Word, nums, alphanums, OneOrMore, Group, Suppress


unit_chars = 'ums'
decimal_chars = nums + '.'
bytes_size_chars = 'kKMmGgbB'
bytes_size_chars_full = decimal_chars + 'kKMmGgbB'

# Latency   196.94ms  183.71ms 944.41ms   89.18%
latency_pattern = Literal('Latency').suppress() \
  + Word(decimal_chars).setResultsName('latency') \
  + Word(unit_chars).setResultsName('latency_unit') \
  + Word(decimal_chars).setResultsName('stdev') \
  + Word(unit_chars).setResultsName('stdev_unit') \
  + Word(decimal_chars).setResultsName('max_value') \
  + Word(unit_chars).setResultsName('max_unit') \
  + Word(decimal_chars).setResultsName('stdev_perc') \
  + Literal('%')

# Running 5s test @ https://foo.org
head_pattern = Literal("Running").suppress() \
  + Word(nums).setResultsName('duration') \
  + Literal('s').setResultsName('duration_unit') \
  + Literal("test @ ").suppress() \
  + Word(alphanums + "/-.:?&=%").setResultsName('url')

# 10 threads and 10 connections
threads_connections_pattern = Word(nums).setResultsName('threads_count') + Literal('threads and').suppress() \
  + Word(nums).setResultsName('connections_count') + Literal('connections').suppress()

# Req/Sec     7.65      2.98    10.00     71.19%
req_sec_pattern = Literal('Req/Sec').suppress() \
  + Word(decimal_chars).setResultsName('req_sec') \
  + Word(decimal_chars).setResultsName('req_sec_stdev') \
  + Word(decimal_chars).setResultsName('req_sec_max') \
  + Word(decimal_chars).setResultsName('req_sec_stdev_perc') + Literal('%')

# 302 requests in 5.07s, 148.32KB read
# 4294 requests in 30.09s, 2.06MB read
reqs_count_pattern = Word(nums).setResultsName('reqs_count') \
                     + Literal('requests').suppress() \
                     + Literal('in').suppress() \
  + Word(decimal_chars).setResultsName('seconds_count') + Literal('s,').suppress() \
  + Word(decimal_chars).setResultsName('total_transfer_read') \
  + Word(bytes_size_chars).setResultsName('total_transfer_read_unit') \
  + Literal('read').suppress()

# Requests/sec:     59.61
reqs_summary_pattern = Literal('Requests/sec:').suppress() \
  + Word(decimal_chars).setResultsName('reqs_per_second_summary')

# Transfer/sec:     29.28KB
transfer_summary_pattern = Literal('Transfer/sec:').suppress() \
  + Word(decimal_chars).setResultsName('transfer_per_second_summary') \
  + Word(bytes_size_chars).setResultsName('transfer_per_second_summary_unit')

# Latency Distribution
latency_statistics_pattern = Literal('Latency Distribution').suppress() \
  + OneOrMore(Group(Word(nums).setResultsName('percentile')
                    + Literal('%').suppress()
                    + Word(decimal_chars).setResultsName('value')
                    + Word(unit_chars).setResultsName('value_unit'))).setResultsName('values')

"""
  Latency Distribution (HdrHistogram - Recorded Latency)
 50.000%  129.15ms
 75.000%  142.46ms
 90.000%  148.09ms
 99.000%  873.98ms
 99.900%  876.54ms
 99.990%  876.54ms
 99.999%  876.54ms
100.000%  876.54ms

"""
hdrhistogram_pattern = Literal('Latency Distribution (HdrHistogram - Recorded Latency)').suppress() \
    + OneOrMore(Group(Word(decimal_chars) + Suppress('%')
                      + Word(decimal_chars).setResultsName('value')
                      + Word(unit_chars).setResultsName('value_unit'))).setResultsName('values')

"""
#[Mean    =      161.908, StdDeviation   =      150.488]
#[Max     =      876.032, Total count    =           80]
#[Buckets =           27, SubBuckets     =         2048]
"""
HASH, LSB, EQUALS, RSB, COMMA = map(Suppress, '#[=],')
decimal_or_nan = decimal_chars + '-nan' + 'inf'
detailed_percentile_spectrum_pattern = Literal('Detailed Percentile spectrum:').suppress() \
    + Literal('Value').suppress() + Literal('Percentile').suppress() \
    + Literal('TotalCount').suppress() + Literal('1/(1-Percentile)').suppress() \
    + OneOrMore(Group(Word(decimal_or_nan).setResultsName('value') +
                      Word(decimal_or_nan).setResultsName('percentile') +
                      Word(nums).setResultsName('total_count') +
                      Word(decimal_or_nan).setResultsName('percentile_1_1'))).setResultsName('values') \
    + HASH + LSB + Suppress('Mean') + EQUALS + Word(decimal_or_nan).setResultsName('mean') \
    + COMMA + Suppress('StdDeviation') \
    + EQUALS + Word(decimal_or_nan).setResultsName('standard_deviation') + RSB \
    + HASH + LSB + Suppress('Max') + EQUALS + Word(decimal_or_nan).setResultsName('max_value') \
    + COMMA + Suppress('Total count') \
    + EQUALS + Word(nums).setResultsName('total_count') + RSB \
    + HASH + LSB + Suppress('Buckets') + EQUALS + Word(decimal_or_nan).setResultsName('buckets') \
    + COMMA + Suppress('SubBuckets') \
    + EQUALS + Word(nums).setResultsName('sub_buckets') + RSB


comma = Literal(',').suppress()

socket_errors_pattern = Literal('Socket errors: connect').suppress() + Word(nums).setResultsName('connect_errors') \
  + comma \
  + Literal('read').suppress() + Word(nums).setResultsName('read_errors') + comma  \
  + Literal('write').suppress() + Word(nums).setResultsName('write_errors') + comma \
  + Literal('timeout').suppress() + Word(nums).setResultsName('timeout_errors') \

# Non-2xx or 3xx responses: 2400
not_successful_responses_pattern = Literal('Non-2xx or 3xx responses:').suppress() \
                                   + Word(nums).setResultsName('non_2xx_or_3xx_responses_count')


start_pattern = head_pattern + threads_connections_pattern


class ParseFailure:

    def __init__(self, exception_message, desired_type, raw_value):
        self.exception_message = exception_message
        self.desired_type = desired_type
        self.raw_value = raw_value

    def to_dict(self):
        return self.__dict__.copy()


class Result:

    def __setattr__(self, key, value):
        if key in self.__dict__:
            raise AttributeError(f'{key} is read only')
        super().__setattr__(key, value)

    def __repr__(self):
        return ' '.join(f'{key}: {value}' for key, value in self.__dict__.items())

    def __eq__(self, other):
        if other.__class__ is not self.__class__:
            return NotImplemented
        return other.__dict__ == self.__dict__

    @classmethod
    def parse(cls, raw: str):
        try:
            values = cls.pattern.parseString(raw)
        except Exception as pex:
            return ParseFailure(str(pex), cls, raw)
        return cls(**values)

    def to_dict(self):
        return self.__dict__.copy()


class ValueResult(Result):

    def __init__(self, value, unit):
        self.value = value
        self.unit = unit.lower()

    def __repr__(self):
        return f'{self.value}{self.unit}'

    def __eq__(self, other):
        if isinstance(other, ValueResult):
            return other.value == self.value and other.unit == self.unit
        return NotImplemented


class TimeResult(ValueResult):

    def __init__(self, value, unit):
        super().__init__(value, unit)
        self.ms = self._to_ms()

    def _to_ms(self):
        if self.unit == 'ms':
            return self.value
        if self.unit == 'us':
            return self.value / 1000
        if self.unit == 's':
            return self.value * 1000


class SocketErrorsResult(Result):

    pattern = socket_errors_pattern

    def __init__(self,
                 connect_errors,
                 read_errors,
                 write_errors,
                 timeout_errors):
        self.connect_errors = int(connect_errors)
        self.read_errors = int(read_errors)
        self.write_errors = int(write_errors)
        self.timeout_errors = int(timeout_errors)


class LatencyResult(Result):

    pattern = latency_pattern

    def __init__(self,
                 latency,
                 latency_unit,
                 stdev,
                 stdev_unit,
                 max_value,
                 max_unit,
                 stdev_perc):
        self.avg = TimeResult(float(latency), latency_unit)
        self.stdev = TimeResult(float(stdev), stdev_unit)
        self.max = TimeResult(float(max_value), max_unit)
        self.stdev_perc = float(stdev_perc)


class LatencyDistributionResult(Result):
    """wrk latency distribution output"""

    pattern = latency_statistics_pattern

    def __init__(self, values):
        percentiles = {}
        for percentile, value, value_unit in values:
            percentiles[float(percentile)] = TimeResult(float(value), value_unit)
        self.percentiles = percentiles

    def __eq__(self, other):
        if isinstance(other, LatencyDistributionResult):
            return self.percentiles == other.percentiles
        if isinstance(other, dict):
            return self.percentiles == other
        return NotImplemented

    @staticmethod
    def line_matches(value: str):
        return 'Latency Distribution' in value and 'HdrHistogram' not in value

    @staticmethod
    def last_line_matches(value: str):
        return '99% ' in value


class HdrHistogramLatencyDistributionResult(LatencyDistributionResult):
    """wrk2 latency distribution output"""

    pattern = hdrhistogram_pattern

    @staticmethod
    def line_matches(value: str):
        return 'Latency Distribution' in value and 'HdrHistogram' in value

    @staticmethod
    def last_line_matches(value: str):
        return '100.000% ' in value


class RequestsSummaryResult(Result):

    pattern = reqs_summary_pattern

    def __init__(self, reqs_per_second_summary):
        self.reqs_per_second_summary = float(reqs_per_second_summary)


class TransferSummaryResult(Result):

    pattern = transfer_summary_pattern

    def __init__(self, transfer_per_second_summary, transfer_per_second_summary_unit):
        self.transfer_per_second_avg = ValueResult(float(transfer_per_second_summary), transfer_per_second_summary_unit)


class RequestsPerSecondResult(Result):

    pattern = req_sec_pattern

    def __init__(self, req_sec, req_sec_stdev, req_sec_max, req_sec_stdev_perc):
        self.avg = float(req_sec)
        self.stdev = float(req_sec_stdev)
        self.max = float(req_sec_max)
        self.stdev_perc = float(req_sec_stdev_perc)


class TotalRequestsResult(Result):

    pattern = reqs_count_pattern

    def __init__(self, reqs_count, seconds_count, total_transfer_read, total_transfer_read_unit):
        self.requests = int(reqs_count)
        self.seconds = float(seconds_count)
        self.read = ValueResult(float(total_transfer_read), total_transfer_read_unit)


class NotSuccessfulResponses(Result):

    pattern = not_successful_responses_pattern

    def __init__(self, non_2xx_or_3xx_responses_count):
        self.non_2xx_or_3xx_responses_count = int(non_2xx_or_3xx_responses_count)


_non_numeric = {'inf', '-inf', 'nan', '-nan', 'nanus', '-nanus'}  # output from wrk


def try_parse(value, num_type):
    if value in _non_numeric:
        return value
    try:
        return num_type(value)
    except ValueError:
        return value


class DetailedPercentileSpectrumValue(Result):

    def __init__(self, value, percentile, total_count, percentile_1_1):
        self.value = try_parse(value, float)
        self.percentile = try_parse(percentile, float)
        self.total_count = try_parse(total_count, int)
        self.percentile_1_1 = try_parse(percentile_1_1, float)


class DetailedPercentileSpectrum(Result):

    pattern = detailed_percentile_spectrum_pattern

    def __init__(self, values, mean, standard_deviation, max_value, total_count, buckets, sub_buckets):
        self.mean = try_parse(mean, float)
        self.standard_deviation = try_parse(standard_deviation, float)
        self.max = try_parse(max_value, float)
        self.total_count = try_parse(total_count, int)
        self.buckets = try_parse(buckets, int)
        self.sub_buckets = try_parse(sub_buckets, int)
        self.values = [DetailedPercentileSpectrumValue(*value) for value in values]

    @staticmethod
    def line_matches(value: str):
        return 'Detailed Percentile spectrum' in value

    @staticmethod
    def last_line_matches(value: str):
        return '#[Buckets' in value


def all_subclasses(_type):
    yield _type
    for sub_type in _type.__subclasses__():
        yield from all_subclasses(sub_type)


def get_lines(raw_output: str):
    lines = {}
    matching_open_lines = False
    matched_lines = []

    for line in raw_output.splitlines():

        if matching_open_lines:
            matched_lines.append(line)

            if result_type.last_line_matches(line):
                lines[result_type] = '\n'.join(matched_lines)
                matched_lines.clear()
                matching_open_lines = False
            continue

        for result_type in all_subclasses(Result):

            if hasattr(result_type, 'line_matches'):
                if not hasattr(result_type, 'last_line_matches'):
                    raise RuntimeError(f'The class {result_type.__name__} implements a `line_matches` method '
                                       f'but no `last_line_matches` property. Define both methods.')
                if result_type.line_matches(line):
                    matched_lines.append(line)
                    matching_open_lines = True
                    break

            elif hasattr(result_type, 'pattern') and result_type.pattern.matches(line):
                # single line
                lines[result_type] = line
    return lines


def _parse_latency_distribution(line_match):
    if LatencyDistributionResult in line_match:
        return LatencyDistributionResult.parse(line_match[LatencyDistributionResult])

    if HdrHistogramLatencyDistributionResult in line_match:
        return HdrHistogramLatencyDistributionResult.parse(line_match[HdrHistogramLatencyDistributionResult])

    return None


LatencyDistributionType = Union[LatencyDistributionResult, HdrHistogramLatencyDistributionResult, None]


class BenchmarkOutput(Result):

    def __init__(self,
                 *,
                 benchmark_id: str = None,
                 raw_output: str = None,
                 url: str = None,
                 threads: Optional[int] = None,
                 connections: Optional[int] = None,
                 latency: Optional[LatencyResult] = None,
                 duration: Optional[ValueResult] = None,
                 socket_errors: Optional[SocketErrorsResult] = None,
                 detailed_percentile_spectrum: Optional[DetailedPercentileSpectrum] = None,
                 not_successful_responses: int = 0,
                 latency_distribution: LatencyDistributionType = None,
                 requests_summary: Optional[RequestsSummaryResult] = None,
                 requests_per_second: Optional[float] = None,
                 transfer_per_second: Optional[float] = None,
                 total: Optional[TotalRequestsResult] = None,
                 suite_id: Optional[str] = None,
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None):
        self.id = benchmark_id or str(uuid4())
        self.raw_output = raw_output
        self.url = url
        self.threads = threads
        self.connections = connections
        self.duration = duration
        self.latency = latency
        self.latency_distribution = latency_distribution
        self.requests_summary = requests_summary,
        self.requests_per_second = requests_per_second
        self.socket_errors = socket_errors
        self.detailed_percentile_spectrum = detailed_percentile_spectrum
        self.not_successful_responses = not_successful_responses
        self.has_errors = bool(socket_errors or not_successful_responses)
        self.transfer_per_second = transfer_per_second
        self.total = total
        self.goals_results = []
        self.suite_id = suite_id
        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self):
        return f'<BenchmarkOutput {self.id} {self.url}>'

    @classmethod
    def parse(cls,
              raw_output: str,
              benchmark_id: Optional[str] = None,
              suite_id: Optional[str] = None,
              start_time: Optional[datetime] = None,
              end_time: Optional[datetime] = None):
        if not benchmark_id:
            benchmark_id = str(uuid4())

        raw_output = raw_output.strip()
        head = start_pattern.parseString(raw_output)

        line_match = get_lines(raw_output)

        duration = TimeResult(int(head.duration), head.duration_unit)
        url = head.url
        threads = int(head.threads_count)
        connections = int(head.connections_count)
        latency = LatencyResult.parse(line_match[LatencyResult]) \
            if LatencyResult in line_match else None
        latency_distribution = _parse_latency_distribution(line_match)

        socket_errors = SocketErrorsResult.parse(line_match[SocketErrorsResult])\
            if SocketErrorsResult in line_match else None

        requests_summary = RequestsPerSecondResult.parse(line_match[RequestsPerSecondResult]) \
            if RequestsPerSecondResult in line_match else None

        requests_per_second = RequestsSummaryResult.parse(line_match[RequestsSummaryResult])\
            .reqs_per_second_summary \
            if RequestsSummaryResult in line_match else None

        transfer_per_second = TransferSummaryResult.parse(line_match[TransferSummaryResult])\
            .transfer_per_second_avg \
            if TransferSummaryResult in line_match else None

        total = TotalRequestsResult.parse(line_match[TotalRequestsResult]) \
            if TotalRequestsResult in line_match else None

        not_successful_responses = NotSuccessfulResponses.parse(line_match[NotSuccessfulResponses])\
            .non_2xx_or_3xx_responses_count \
            if NotSuccessfulResponses in line_match else 0

        detailed_percentile_spectrum = DetailedPercentileSpectrum.parse(line_match[DetailedPercentileSpectrum])\
            if DetailedPercentileSpectrum in line_match else None

        return cls(benchmark_id=benchmark_id,
                   raw_output=raw_output,
                   url=url,
                   threads=threads,
                   connections=connections,
                   latency=latency,
                   duration=duration,
                   socket_errors=socket_errors,
                   not_successful_responses=not_successful_responses,
                   detailed_percentile_spectrum=detailed_percentile_spectrum,
                   latency_distribution=latency_distribution,
                   requests_summary=requests_summary,
                   requests_per_second=requests_per_second,
                   transfer_per_second=transfer_per_second,
                   total=total,
                   suite_id=suite_id,
                   start_time=start_time,
                   end_time=end_time)

    def to_dict(self):
        data = super().to_dict()
        data['raw_output'] = data['raw_output'].splitlines()
        return data

