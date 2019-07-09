import ssl
import certifi

SECURE_SSLCONTEXT = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=certifi.where())
SECURE_SSLCONTEXT.check_hostname = True

INSECURE_SSLCONTEXT = ssl.SSLContext()
INSECURE_SSLCONTEXT.check_hostname = False


ssl_verify = True


def get_ssl_context() -> ssl.SSLContext:
    global ssl_verify

    if ssl_verify:
        return SECURE_SSLCONTEXT

    return INSECURE_SSLCONTEXT


def disable_ssl_verification():
    global ssl_verify
    ssl_verify = False

