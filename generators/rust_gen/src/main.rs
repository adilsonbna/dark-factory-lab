use opentelemetry::{global, KeyValue};
use opentelemetry_otlp::WithExportConfig;
use opentelemetry_sdk::metrics::SdkMeterProvider;
use opentelemetry_sdk::{runtime, Resource};
use std::time::Duration;

fn init_meter_provider() -> SdkMeterProvider {
    let resource = Resource::new(vec![KeyValue::new("service.name", "rust-generator")]);
    opentelemetry_otlp::new_pipeline()
        .metrics(runtime::Tokio)
        .with_exporter(
            opentelemetry_otlp::new_exporter()
                .tonic()
                .with_endpoint("http://otel-collector:4317"),
        )
        .with_resource(resource)
        .with_period(Duration::from_secs(5))
        .build()
        .expect("failed to build OTLP metrics meter provider")
}

#[tokio::main]
async fn main() {
    let meter_provider = init_meter_provider();
    global::set_meter_provider(meter_provider.clone());
    let meter = global::meter("rust-generator");
    let counter = meter
        .u64_counter("requests_total_rust")
        .with_description("Simulated requests from Rust generator")
        .init();

    println!("Rust Telemetry Generator starting (OTLP/gRPC -> otel-collector:4317)...");
    loop {
        counter.add(1, &[]);
        println!("Emitted metric (Rust): requests_total_rust +1");
        tokio::time::sleep(Duration::from_secs(5)).await;
    }
}
