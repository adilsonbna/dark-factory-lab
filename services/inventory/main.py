from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_tracer

resource = Resource(attributes={"service.name": "inventory"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces"))
)
trace.set_tracer_provider(provider)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

tracer = get_tracer("inventory")

ITEMS = {
    "sku-100": {"name": "widget", "price": 9.99},
    "sku-200": {"name": "gadget", "price": 24.50},
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items/{item_id}")
def get_item(item_id: str):
    with tracer.start_as_current_span("lookup_item", attributes={"item.id": item_id}):
        item = ITEMS.get(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="item not found")
        return item
