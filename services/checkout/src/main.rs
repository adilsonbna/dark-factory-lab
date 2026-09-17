use axum::{http::StatusCode, routing::get, routing::post, Json, Router};
use opentelemetry::propagation::Injector;
use opentelemetry::trace::{Span, TraceContextExt, Tracer};
use opentelemetry::{global, KeyValue};
use opentelemetry_otlp::WithExportConfig;
use opentelemetry_sdk::propagation::TraceContextPropagator;
use opentelemetry_sdk::trace::TracerProvider;
use opentelemetry_sdk::{runtime, Resource};
use reqwest::header::{HeaderMap, HeaderName, HeaderValue};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::net::SocketAddr;
use std::sync::atomic::{AtomicU64, Ordering};

const INVENTORY_URL: &str = "http://inventory:8082";
static ORDER_COUNTER: AtomicU64 = AtomicU64::new(0);

fn init_tracer() -> TracerProvider {
    global::set_text_map_propagator(TraceContextPropagator::new());
    let resource = Resource::new(vec![KeyValue::new("service.name", "checkout")]);
    let provider = opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_exporter(
            opentelemetry_otlp::new_exporter()
                .tonic()
                .with_endpoint("http://otel-collector:4317"),
        )
        .with_trace_config(opentelemetry_sdk::trace::Config::default().with_resource(resource))
        .install_batch(runtime::Tokio)
        .expect("failed to install OTLP tracer provider");

    global::set_tracer_provider(provider.clone());
    provider
}

struct HeaderInjector<'a>(&'a mut HeaderMap);

impl<'a> Injector for HeaderInjector<'a> {
    fn set(&mut self, key: &str, value: String) {
        if let (Ok(k), Ok(v)) = (
            HeaderName::from_bytes(key.as_bytes()),
            HeaderValue::from_str(&value),
        ) {
            self.0.insert(k, v);
        }
    }
}

#[derive(Deserialize)]
struct OrderRequest {
    item_id: String,
    quantity: u32,
}

#[derive(Serialize)]
struct OrderResponse {
    order_id: String,
    item: Value,
    quantity: u32,
}

async fn health() -> &'static str {
    "ok"
}

async fn create_order(Json(body): Json<OrderRequest>) -> (StatusCode, Json<Value>) {
    let tracer = global::tracer("checkout");
    let span = tracer.start("checkout.create_order");
    let cx = opentelemetry::Context::current_with_span(span);

    let mut headers = HeaderMap::new();
    global::get_text_map_propagator(|p| {
        p.inject_context(&cx, &mut HeaderInjector(&mut headers));
    });

    let client = Client::new();
    let url = format!("{}/items/{}", INVENTORY_URL, body.item_id);

    let resp = match client.get(&url).headers(headers).send().await {
        Ok(r) => r,
        Err(e) => {
            cx.span().end();
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(serde_json::json!({"error": e.to_string()})),
            );
        }
    };

    if !resp.status().is_success() {
        cx.span().end();
        return (
            StatusCode::BAD_GATEWAY,
            Json(serde_json::json!({"error": format!("inventory returned {}", resp.status())})),
        );
    }

    let item: Value = match resp.json().await {
        Ok(v) => v,
        Err(e) => {
            cx.span().end();
            return (
                StatusCode::BAD_GATEWAY,
                Json(serde_json::json!({"error": e.to_string()})),
            );
        }
    };

    let order = OrderResponse {
        order_id: format!("ord-{}", ORDER_COUNTER.fetch_add(1, Ordering::Relaxed)),
        item,
        quantity: body.quantity,
    };

    cx.span().end();
    (StatusCode::OK, Json(serde_json::to_value(order).unwrap()))
}

#[tokio::main]
async fn main() {
    let _provider = init_tracer();

    let app = Router::new()
        .route("/health", get(health))
        .route("/orders", post(create_order));

    let addr = SocketAddr::from(([0, 0, 0, 0], 8081));
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    println!("checkout listening on {addr}");
    axum::serve(listener, app).await.unwrap();
}
