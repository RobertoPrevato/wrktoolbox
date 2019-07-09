import pytest
from wrktoolbox.plugins.clientip import capture_ips, is_valid_ip_address


@pytest.mark.parametrize('text,expected_result', [
    ['Hello 2001:0db8:0000:0000:0000:8a2e:0370:7334', ['2001:0db8:0000:0000:0000:8a2e:0370:7334']],
    ['Hello 2001:0db8:0000:0000:0000:8a2e:0370:7334 World 2001:db8::8a2e:370:7334',
     ['2001:0db8:0000:0000:0000:8a2e:0370:7334', '2001:db8::8a2e:370:7334']],
    ['172.16.254.1', ['172.16.254.1']],
    ['172.16.254.1 2001:0db8:0000:0000:0000:8a2e:0370:7334',
     ['172.16.254.1', '2001:0db8:0000:0000:0000:8a2e:0370:7334']]
])
def test_extract_ips(text, expected_result):
    result = capture_ips(text)
    assert result == expected_result


@pytest.mark.parametrize('value,expected_result', [
    ['172.16.254.1', True],
    ['2001:0db8:0000:0000:0000:8a2e:0370:7334', True],
    ['Hello World', False],
    ['172.16.254.1X', False]
])
def test_is_valid_ip_address(value, expected_result):
    assert is_valid_ip_address(value) == expected_result
