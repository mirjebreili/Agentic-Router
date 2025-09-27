import pytest

from agentic_router.nodes.utils import build_service_url


@pytest.mark.parametrize(
    "host, port, endpoint, expected",
    [
        ("example.com", 8080, "/assistants/search", "http://example.com:8080/assistants/search"),
        (
            "https://example.com",
            443,
            "assistants/search",
            "https://example.com:443/assistants/search",
        ),
        (
            "https://example.com:9000",
            8080,
            "/a2a/agent",
            "https://example.com:9000/a2a/agent",
        ),
        (
            "https://example.com/base",
            9000,
            "assistants/search",
            "https://example.com:9000/base/assistants/search",
        ),
        (
            "example.com:7000",
            8080,
            "a2a/agent",
            "http://example.com:7000/a2a/agent",
        ),
        (
            "https://[2001:db8::1]",
            9000,
            "assistants/search",
            "https://[2001:db8::1]:9000/assistants/search",
        ),
    ],
)
def test_build_service_url(host, port, endpoint, expected):
    assert build_service_url(host, port, endpoint) == expected


def test_build_service_url_requires_hostname_with_protocol():
    with pytest.raises(ValueError):
        build_service_url("https://", 8000, "/assistants/search")


def test_build_service_url_rejects_empty_host():
    with pytest.raises(ValueError):
        build_service_url("", 8000, "/assistants/search")
