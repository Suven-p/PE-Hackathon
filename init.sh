# Add packages for OpenTelemetry
uv add opentelemetry-distro opentelemetry-exporter-otlp
uv run opentelemetry-bootstrap -a requirements | uv add --requirement -
