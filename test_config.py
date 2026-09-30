import pytest
from pydantic import ValidationError

from app.core.config import Settings

GOOD = "x" * 40
OTHER = "y" * 40


def make(**kw):
    base = dict(ENVIRONMENT="test", _env_file=None)
    base.update(kw)
    return Settings(**base)


def test_test_env_allows_empty_secrets():
    make()


def test_rejects_wildcard_cors():
    with pytest.raises(ValidationError):
        make(CORS_ORIGINS="*")


def test_production_requires_strong_distinct_secrets():
    prod = dict(ENVIRONMENT="production", DATABASE_URL="postgresql://u:p@db/x",
                CORS_ORIGINS="https://app.example.org")
    with pytest.raises(ValidationError):
        make(**prod, SECRET_KEY="short", MODEL_SIGNING_KEY=OTHER)
    with pytest.raises(ValidationError):
        make(**prod, SECRET_KEY=GOOD, MODEL_SIGNING_KEY=GOOD)
    make(**prod, SECRET_KEY=GOOD, MODEL_SIGNING_KEY=OTHER)


def test_production_rejects_debug_and_http_cors():
    base = dict(ENVIRONMENT="production", DATABASE_URL="postgresql://u:p@db/x",
                SECRET_KEY=GOOD, MODEL_SIGNING_KEY=OTHER)
    with pytest.raises(ValidationError):
        make(**base, CORS_ORIGINS="https://a.org", DEBUG=True)
    with pytest.raises(ValidationError):
        make(**base, CORS_ORIGINS="http://a.org")


def test_error_message_never_contains_secret_value():
    leak_probe = "zzprobezzvaluezzshort"
    with pytest.raises(ValidationError) as e:
        make(ENVIRONMENT="production", SECRET_KEY="short"+leak_probe, MODEL_SIGNING_KEY=OTHER,
             DATABASE_URL="postgresql://u:p@db/x", CORS_ORIGINS="https://a.org")
    assert leak_probe not in str(e.value)
