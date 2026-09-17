import time

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

resource = Resource(attributes={"service.name": "python-generator"})
exporter = OTLPMetricExporter(endpoint="http://otel-collector:4318/v1/metrics")
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)

meter = metrics.get_meter("python-generator")
requests_counter = meter.create_counter("requests_total", description="Simulated requests")


def run():
    print("Python Telemetry Generator starting (OTLP/HTTP -> otel-collector:4318)...")
    while True:
        requests_counter.add(1)
        print("Emitted metric: requests_total +1")
        time.sleep(5)


if __name__ == "__main__":
    run()
