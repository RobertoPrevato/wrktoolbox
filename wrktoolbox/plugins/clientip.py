import re
import os
import socket
import urllib.request
from logging import Logger
from wrktoolbox.web import get_ssl_context
from wrktoolbox.benchmarks import BenchmarkSuite
from rocore.decorators import retry


def capture_ips(text: str):
    return re.findall(r'[0-9]+(?:\.[0-9]+){3}', text) + re.findall(r'\b(?:(?:[0-9a-zA-Z]{1,4}|:):?){8}\b', text)


def is_valid_ipv4_address(value):
    try:
        socket.inet_aton(value)
    except socket.error:
        return False
    return True


def is_valid_ipv6_address(value):
    try:
        socket.inet_pton(socket.AF_INET6, value)
    except socket.error:
        return False
    return True


def is_valid_ip_address(value):
    return is_valid_ipv4_address(value) or is_valid_ipv6_address(value)


class IpAddressNotFoundInResponseBody(Exception):

    def __init__(self, source_url, response_body):
        super().__init__('A valid IP address could not be extracted from response body, using configured source url.')
        self.source_url = source_url
        self.response_body = response_body


class InvalidIpAddress(Exception):

    def __init__(self, value):
        super().__init__('The value obtained from configured source url, does not represent a valid IP address.')
        self.value = value


def get_public_ip_address(source_url):
    response = urllib.request.urlopen(source_url, context=get_ssl_context())
    text = response.read().decode('utf8')

    captured_ips = capture_ips(text)

    if not captured_ips:
        raise IpAddressNotFoundInResponseBody(source_url, text)

    value = captured_ips[0]

    if not is_valid_ip_address(value):
        raise InvalidIpAddress(value)

    return value


def setup(suite: BenchmarkSuite, logger: Logger):
    if suite.metadata is None:
        suite.metadata = {}

    source_url = suite.metadata.get('client_ip_source_url',
                                    os.environ.get('WRKTOOLBOX_CLIENT_IP_SOURCE_URL', 'https://api.ipify.org'))

    logger.info('Obtaining client ip address, using source url: %s', source_url)

    def log_retry(exc, attempt):
        if attempt > 3:
            return
        logger.exception('Attempt to obtain public ip address failed; %s', attempt, exc_info=exc)

    @retry(delay=0.5, on_exception=log_retry)
    def get_ip():
        return get_public_ip_address(source_url)

    # noinspection PyBroadException
    try:
        client_ip = get_ip()
    except Exception:
        logger.info('Failed to obtain public ip address')
        suite.public_ip = '???'
    else:
        logger.info('Public client ip: %s', client_ip)
        suite.public_ip = client_ip
