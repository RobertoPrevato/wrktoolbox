import reprlib
from typing import Union
from wrktoolbox.benchmarks import PerformanceGoal, GoalException
from wrktoolbox.wrkoutput import BenchmarkOutput
from .common import LimitType


PercentileType = Union[int, float, str]


class AverageLatencyGoal(PerformanceGoal):
    """A performance goal that is satisfied when the overall average latency
    is lower than a given limit, in milliseconds"""

    type_name = 'avg-latency'

    def __init__(self, limit: LimitType):
        """
        Creates a new instance of AverageLatencyGoal with given limit in ms.

        :param limit: average latency limit in milliseconds
        """
        self.limit = float(limit)

    def __repr__(self):
        return f'Average latency for web requests must be less than {self.limit} ms.'

    def is_satisfied(self, output: BenchmarkOutput) -> bool:
        self.assert_parsed(output.latency)
        return output.latency.avg.ms <= self.limit


class PercentileLatencyGoal(PerformanceGoal):
    """A performance goal that is satisfied when the percentile latency of web requests is less than a limit in ms."""

    type_name = 'percentile-latency'

    def __init__(self, percentile: PercentileType, limit: LimitType):
        """
        Creates a new instance of PercentileLatencyGoal with given percentile and limit in ms.

        :param percentile: reference percentile of this goal
        :param limit: average latency limit in milliseconds
        """
        self.percentile = float(percentile)
        self.limit = limit

    def __repr__(self):
        return f'The {self.percentile} percentile latency of web requests must be less than {self.limit} ms.'

    def is_satisfied(self, output: BenchmarkOutput) -> bool:
        self.assert_parsed(output.latency_distribution)
        value = output.latency_distribution.percentiles.get(self.percentile)

        if value is None:
            raise GoalException(f'Percentile {self.percentile} is not found among output percentiles, '
                                f'therefore it`s not possible to use an exact value. '
                                f'Configure performance goals to use percentiles returned by wrk. '
                                f'Found percentiles are: {reprlib.repr(output.latency_distribution.percentiles)}')

        return value.ms <= self.limit

