from typing import Union
from wrktoolbox.benchmarks import PerformanceGoal
from wrktoolbox.wrkoutput import BenchmarkOutput


LimitType = Union[int, float, str]


class NoSocketErrorsGoal(PerformanceGoal):
    """A goal that is satisfied if there are no socket errors.
    Note that timeout errors can easily occur if wrk timeout is set to a small value."""

    type_name = 'no-socket-errors'

    def is_satisfied(self, output: BenchmarkOutput) -> bool:
        return output.socket_errors is None

    def __repr__(self):
        return 'No socket errors'


class NoFailedRequestsGoal(PerformanceGoal):
    """A goal that is satisfied if there are no responses with non-2xx and non-3xx status"""

    type_name = 'no-failed-requests'

    def is_satisfied(self, output: BenchmarkOutput) -> bool:
        return not output.not_successful_responses

    def __repr__(self):
        return 'No responses with status not in 2xx or 3xx'


class NoErrorsGoal(PerformanceGoal):
    """A goal that is satisfied if there are no errors:
    no socket errors and no responses with status not in 2xx or 3xx."""

    type_name = 'no-errors'

    def is_satisfied(self, output: BenchmarkOutput) -> bool:
        return not (output.not_successful_responses or output.socket_errors)

    def __repr__(self):
        return 'No socket errors and no responses with status not in 2xx or 3xx'


class RequestsPerSecondsGoal(PerformanceGoal):
    """A performance goal satisfied when the number of handled requests
    per second is equals or higher than a given value"""

    type_name = 'requests-per-second'

    def __init__(self, minimum: LimitType):
        self.minimum = float(minimum)

    def is_satisfied(self, output: BenchmarkOutput) -> bool:
        return output.requests_per_second >= self.minimum

    def __repr__(self):
        return f'The minimum amount of handled requests per seconds is {self.minimum}'
