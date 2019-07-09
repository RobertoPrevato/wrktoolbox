import pytest
from pytest import raises
from wrktoolbox.goals import PercentileLatencyGoal, BenchmarkOutput, GoalException, NoErrorsGoal
from wrktoolbox.wrkoutput import LatencyDistributionResult, HdrHistogramLatencyDistributionResult, SocketErrorsResult


@pytest.mark.parametrize('output,percentile,limit,expected_result', [
    [
        BenchmarkOutput(latency_distribution=LatencyDistributionResult(
            [
                [50, 911.84, 'ms'],
                [75, 1.44, 's'],
                [90, 1.50, 's'],
                [99, 1.54, 's']
            ]
        )), 90, 500, False
    ],
    [
        BenchmarkOutput(latency_distribution=LatencyDistributionResult(
            [
                [50, 111.84, 'ms'],
                [75, 200.12, 'ms'],
                [90, 333.50, 'ms'],
                [99, 556.54, 'ms']
            ]
        )), 90, 400, True
    ],
    [
        BenchmarkOutput(latency_distribution=HdrHistogramLatencyDistributionResult(
            [
                [50.000, 129.15, 'ms'],
                [75.000, 142.46, 'ms'],
                [90.000, 148.09, 'ms'],
                [99.000, 837.98, 'ms'],
                [99.900, 873.98, 'ms'],
                [99.990, 883.98, 'ms'],
                [99.999, 883.98, 'ms'],
                [100.000, 893.98, 'ms']
            ]
        )), 90, 400, True
    ]
])
def test_percentile_latency_goal(output, percentile, limit, expected_result):
    goal = PercentileLatencyGoal(percentile, limit)
    assert goal.is_satisfied(output) == expected_result


def test_percentile_goal_raises_for_missing_percentile():
    goal = PercentileLatencyGoal(55, 300)

    with raises(GoalException, match='Percentile 55.0 is not found among output percentiles,'):
        goal.is_satisfied(output=BenchmarkOutput(latency_distribution=LatencyDistributionResult(
            [
                [50, 111.84, 'ms'],
                [75, 200.12, 'ms'],
                [90, 333.50, 'ms'],
                [99, 556.54, 'ms']
            ]
        )))


@pytest.mark.parametrize('output,expected_result', [
    [BenchmarkOutput(socket_errors=SocketErrorsResult(0, 1, 0, 1)), False],
    [BenchmarkOutput(not_successful_responses=20), False],
    [BenchmarkOutput(), True]
])
def test_no_errors_goal(output, expected_result):
    goal = NoErrorsGoal()
    assert goal.is_satisfied(output) == expected_result
