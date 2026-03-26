"""Unit tests for configure_telemetry.

These tests do not require Doppler credentials — all OTel SDK calls are mocked
so no real gRPC connection is attempted.
"""

from unittest.mock import patch

from fastapi import FastAPI

from app.context import ENV_CONTEXT
from app.telemetry import configure_telemetry


def test_noop_without_endpoint(monkeypatch):
    """configure_telemetry is a no-op when OTEL_EXPORTER_OTLP_ENDPOINT is absent."""
    monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)
    app = FastAPI()
    with patch('app.telemetry.trace') as mock_trace:
        configure_telemetry(app)
    mock_trace.set_tracer_provider.assert_not_called()


def test_instrumentors_called(monkeypatch):
    """All three instrumentors are wired when OTEL_EXPORTER_OTLP_ENDPOINT is set."""
    monkeypatch.setenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317')
    app = FastAPI()
    with (
        patch('app.telemetry.OTLPSpanExporter'),
        patch('app.telemetry.trace'),
        patch('app.telemetry.RequestsInstrumentor') as mock_req,
        patch('app.telemetry.LoggingInstrumentor') as mock_log,
        patch('app.telemetry.FastAPIInstrumentor') as mock_fastapi,
    ):
        configure_telemetry(app)

    mock_req.return_value.instrument.assert_called_once()
    mock_log.return_value.instrument.assert_called_once_with(set_logging_format=False)
    mock_fastapi.instrument_app.assert_called_once_with(app)


def test_resource_attributes_match_env_context(monkeypatch):
    """OTel Resource is built from ENV_CONTEXT so span metadata matches wide events."""
    monkeypatch.setenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317')
    app = FastAPI()
    with (
        patch('app.telemetry.OTLPSpanExporter'),
        patch('app.telemetry.trace'),
        patch('app.telemetry.RequestsInstrumentor'),
        patch('app.telemetry.LoggingInstrumentor'),
        patch('app.telemetry.FastAPIInstrumentor'),
        patch('app.telemetry.TracerProvider') as mock_provider,
    ):
        configure_telemetry(app)

    resource = mock_provider.call_args.kwargs['resource']
    attrs = resource.attributes
    assert attrs['service.name'] == ENV_CONTEXT['service']
    assert attrs['service.version'] == ENV_CONTEXT['version']
    assert attrs['deployment.environment'] == ENV_CONTEXT['environment']
    assert attrs['service.instance.id'] == ENV_CONTEXT['instance_id']
    assert attrs['service.commit'] == ENV_CONTEXT['commit_sha']
