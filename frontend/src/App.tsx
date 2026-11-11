import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type OrderForm = {
  customer_email: string;
  item: string;
  quantity: string;
  amount_cents: string;
};
type Order = {
  id: number;
  item: string;
  quantity: number;
  amount_cents: number;
  status: string;
  createdAt: string;
  latency: number;
  traceId: string;
  error?: string;
};
type Call = { latency: number; status: number; time: number };
type TapeEvent = { time: string; kind: "M" | "L" | "T"; name: string; detail: string; traceId?: string };

const initialForm: OrderForm = { customer_email: "", item: "", quantity: "1", amount_cents: "199" };
const drillEmail = ["drill", "example", "test"].join("@");
const grafanaUrl = import.meta.env.VITE_GRAFANA_URL as string | undefined;
const tempoBase = import.meta.env.VITE_TEMPO_BASE as string | undefined;

function traceparent() {
  const bytes = new Uint8Array(24);
  crypto.getRandomValues(bytes);
  const trace = [...bytes].map((value) => value.toString(16).padStart(2, "0")).join("");
  return `00-${trace.slice(0, 32)}-${trace.slice(32)}-01`;
}

function timeLabel(date = new Date()) {
  return date.toLocaleTimeString([], { hour12: false }) + `.${String(date.getMilliseconds()).padStart(3, "0")}`;
}

function statusClass(status: number) {
  return `${Math.floor(status / 100)}xx`;
}

function latencyHeight(latency: number) {
  return `height-${Math.min(10, Math.max(1, Math.ceil(latency / 40)))}`;
}

export function App() {
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [orders, setOrders] = useState<Order[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);
  const [tape, setTape] = useState<TapeEvent[]>([]);
  const [health, setHealth] = useState<"Healthy" | "Degraded" | "Down">("Degraded");
  const [healthLatency, setHealthLatency] = useState<number | null>(null);
  const [notice, setNotice] = useState("");
  const [drilling, setDrilling] = useState(false);
  const [tapeOpen, setTapeOpen] = useState(true);
  const [burstCount, setBurstCount] = useState("30");
  const [burstRate, setBurstRate] = useState("5");
  const session = useRef(crypto.randomUUID());
  const telemetry = useRef<unknown[]>([]);
  const stopDrill = useRef(false);

  const addTape = useCallback((event: Omit<TapeEvent, "time">) => {
    setTape((current) => [{ ...event, time: timeLabel() }, ...current].slice(0, 100));
  }, []);

  const sendTelemetry = useCallback((event: Record<string, unknown>) => {
    telemetry.current.push(event);
    if (telemetry.current.length >= 20) void flushTelemetry();
  }, []);

  const flushTelemetry = useCallback(async () => {
    if (!telemetry.current.length) return;
    const events = telemetry.current.splice(0, 50);
    try {
      await fetch("/api/telemetry", {
        method: "POST",
        headers: { "content-type": "application/json", traceparent: traceparent() },
        body: JSON.stringify({ session: session.current, route: "console", events }),
        keepalive: true,
      });
    } catch {
      // Telemetry must not affect the order flow.
    }
  }, []);

  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === "hidden") void flushTelemetry();
    };
    const onError = () => sendTelemetry({ type: "error", kind: "error" });
    const onRejection = () => sendTelemetry({ type: "error", kind: "unhandledrejection" });
    window.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onRejection);
    sendTelemetry({ type: "event", name: "page_view" });
    return () => {
      void flushTelemetry();
      window.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onRejection);
    };
  }, [flushTelemetry, sendTelemetry]);

  useEffect(() => {
    const timer = window.setInterval(() => void flushTelemetry(), 5000);
    const navigation = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
    if (navigation) sendTelemetry({ type: "vital", name: "TTFB", value: navigation.responseStart / 1000 });
    const observers: PerformanceObserver[] = [];
    const observe = (type: string, handler: (entry: PerformanceEntry) => void, options?: PerformanceObserverInit) => {
      if (!("PerformanceObserver" in window)) return;
      try {
        const observer = new PerformanceObserver((list) => list.getEntries().forEach(handler));
        observer.observe({ type, buffered: true });
        observers.push(observer);
      } catch {
        // Older browsers can omit individual performance entry types.
      }
    };
    observe("paint", (entry) => {
      if (entry.name === "first-contentful-paint") sendTelemetry({ type: "vital", name: "FCP", value: entry.startTime / 1000 });
    });
    observe("largest-contentful-paint", (entry) => sendTelemetry({ type: "vital", name: "LCP", value: entry.startTime / 1000 }));
    observe("event", (entry) => {
      const duration = (entry as PerformanceEventTiming).duration;
      if (duration > 0) sendTelemetry({ type: "vital", name: "INP", value: duration / 1000 });
    });
    return () => {
      window.clearInterval(timer);
      observers.forEach((observer) => observer.disconnect());
    };
  }, [flushTelemetry, sendTelemetry]);

  const checkHealth = useCallback(async () => {
    const started = performance.now();
    try {
      const response = await fetch("/health", { headers: { traceparent: traceparent() } });
      const latency = performance.now() - started;
      sendTelemetry({ type: "api", endpoint: "health", status: response.status, status_class: statusClass(response.status), duration: latency / 1000 });
      setHealth(response.ok ? "Healthy" : "Degraded");
      setHealthLatency(latency);
    } catch {
      setHealth("Down");
      setHealthLatency(null);
    }
  }, []);

  useEffect(() => {
    void checkHealth();
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void checkHealth();
    }, 10000);
    return () => window.clearInterval(timer);
  }, [checkHealth]);

  const p95 = useMemo(() => {
    if (!calls.length) return null;
    const sorted = calls.map((call) => call.latency).sort((a, b) => a - b);
    return sorted[Math.min(sorted.length - 1, Math.ceil(sorted.length * 0.95) - 1)];
  }, [calls]);
  const counts = useMemo(
    () => calls.reduce((result, call) => ({ ...result, [statusClass(call.status)]: (result[statusClass(call.status)] || 0) + 1 }), {} as Record<string, number>),
    [calls],
  );

  async function submitOrder(event?: React.FormEvent, override?: OrderForm, simulateFailure = false) {
    event?.preventDefault();
    const submittedForm = override || form;
    const nextErrors: Record<string, string> = {};
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(submittedForm.customer_email)) nextErrors.customer_email = "Enter a valid email address.";
    if (!submittedForm.item || submittedForm.item.length > 100) nextErrors.item = "Enter an item from 1 to 100 characters.";
    const quantity = Number(submittedForm.quantity);
    const amount = Number(submittedForm.amount_cents);
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 1000) nextErrors.quantity = "Use a whole number from 1 to 1000.";
    if (!Number.isInteger(amount) || amount < 0) nextErrors.amount_cents = "Use a whole number of cents, zero or higher.";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return false;

    const started = performance.now();
    const parent = traceparent();
    const traceId = parent.slice(3, 35);
    sendTelemetry({ type: "event", name: "order_submit" });
    addTape({ kind: "M", name: "frontend_events_total", detail: "order_submit route=console", traceId });
    try {
      const url = simulateFailure ? "/api/orders?simulate_failure=true" : "/api/orders";
      const response = await fetch(url, {
        method: "POST",
        headers: { "content-type": "application/json", traceparent: parent },
        body: JSON.stringify({ ...submittedForm, quantity, amount_cents: amount }),
      });
      const latency = performance.now() - started;
      const call = { latency, status: response.status, time: Date.now() };
      setCalls((current) => [...current.slice(-59), call]);
      sendTelemetry({ type: "api", endpoint: "orders", status: response.status, status_class: statusClass(response.status), duration: latency / 1000, trace: traceId });
      addTape({ kind: "T", name: "POST /api/orders", detail: `${statusClass(response.status)} ${Math.round(latency)}ms`, traceId });
      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: "The API returned an error." }));
        const message = body.detail || "The API returned an error.";
        setNotice(`The API returned ${response.status}. ${message} Try again or run the failure drill to see it.`);
        sendTelemetry({ type: "event", name: "order_failure", trace: traceId });
        addTape({ kind: "L", name: "log", detail: `order_failure reason=${message}`, traceId });
        setOrders((current) => [{ id: Date.now(), item: submittedForm.item, quantity, amount_cents: amount, status: "failed", createdAt: timeLabel(), latency, traceId, error: message }, ...current]);
        return false;
      }
      const data = await response.json();
      sendTelemetry({ type: "event", name: "order_success", trace: traceId });
      addTape({ kind: "L", name: "log", detail: `order_success order_id=${data.id}`, traceId });
      setOrders((current) => [{ ...data, createdAt: timeLabel(), latency, traceId }, ...current]);
      setNotice("");
      return true;
    } catch {
      setNotice("The API is unavailable. Check the health status and try again.");
      return false;
    }
  }

  async function runBurst(failure = false) {
    if (drilling) return;
    const count = Math.min(100, Math.max(1, Number(burstCount) || 30));
    const rate = Math.min(10, Math.max(1, Number(burstRate) || 5));
    setDrilling(true);
    stopDrill.current = false;
    sendTelemetry({ type: "event", name: "drill_start" });
    for (let index = 0; index < count && !stopDrill.current; index += 1) {
      const drillForm = { customer_email: drillEmail, item: "drill-widget", quantity: "1", amount_cents: "199" };
      await submitOrder(undefined, drillForm, failure);
      if (index + 1 < count) await new Promise((resolve) => window.setTimeout(resolve, 1000 / rate));
    }
    sendTelemetry({ type: "event", name: "drill_end" });
    setDrilling(false);
  }

  const copyTrace = async (traceId: string) => {
    await navigator.clipboard.writeText(traceId);
    setNotice("Trace id copied.");
  };

  return (
    <div className="shell">
      <header className="topbar">
        <div className="wordmark">Order Console</div>
        <div className="top-actions">
          <span className={`status-chip ${health.toLowerCase()}`}><i /> API {health}</span>
          <span className="metric-chip">Client p95 <strong>{p95 ? `${Math.round(p95)} ms` : "No calls"}</strong></span>
          {grafanaUrl && <a className="text-link" href={grafanaUrl} target="_blank" rel="noreferrer" onClick={() => sendTelemetry({ type: "event", name: "link_out" })}>Open Grafana</a>}
        </div>
      </header>
      <div className="heartbeat" aria-label="Recent health latency"><svg viewBox="0 0 600 24" preserveAspectRatio="none"><polyline points={calls.map((call, index) => `${index * 10},${Math.max(2, 24 - Math.min(22, call.latency / 10))}`).join(" ")} /></svg></div>
      <main id="main">
        <div className="layout">
          <section className="column">
            <article className="card">
              <div className="card-heading"><div><p className="eyebrow">Real API request</p><h1>Place an order</h1></div><span className="health-latency">{healthLatency ? `${Math.round(healthLatency)} ms` : "Waiting"}</span></div>
              <form onSubmit={submitOrder} noValidate>
                <Field label="Customer email" name="customer_email" type="email" autoComplete="email" value={form.customer_email} error={errors.customer_email} onChange={(value) => setForm({ ...form, customer_email: value })} />
                <Field label="Item" name="item" value={form.item} error={errors.item} onChange={(value) => setForm({ ...form, item: value })} />
                <div className="two-fields">
                  <Field label="Quantity" name="quantity" type="number" value={form.quantity} error={errors.quantity} onChange={(value) => setForm({ ...form, quantity: value })} />
                  <Field label="Amount (cents)" name="amount_cents" type="number" value={form.amount_cents} error={errors.amount_cents} onChange={(value) => setForm({ ...form, amount_cents: value })} />
                </div>
                <button className="button primary" type="submit">Place order</button>
                {notice && <p className="inline-notice" role="status">{notice}</p>}
              </form>
            </article>
            <article className="card">
              <div className="card-heading"><div><p className="eyebrow">Controlled traffic</p><h2>Load drills</h2></div>{drilling && <button className="button danger" onClick={() => { stopDrill.current = true; }}>Stop drill</button>}</div>
              <div className="drill-grid"><button className="button secondary" onClick={() => void submitOrder(undefined, { customer_email: drillEmail, item: "demo-widget", quantity: "1", amount_cents: "199" })}>Send one order</button><button className="button secondary" disabled={drilling} onClick={() => void runBurst()}>Send burst</button><button className="button secondary danger-text" disabled={drilling} onClick={() => void runBurst(true)}>Run failure drill</button></div>
              <div className="drill-inputs"><label>Count<input value={burstCount} onChange={(event) => setBurstCount(event.target.value)} inputMode="numeric" /></label><label>Rate per second<input value={burstRate} onChange={(event) => setBurstRate(event.target.value)} inputMode="numeric" /></label></div>
              <div className="latency-strip" aria-label="Last 60 client calls">{calls.map((call, index) => <span key={`${call.time}-${index}`} className={`${statusClass(call.status)} ${latencyHeight(call.latency)}`} />)}</div>
              <div className="call-counts"><span>2xx <b>{counts["2xx"] || 0}</b></span><span>4xx <b>{counts["4xx"] || 0}</b></span><span>5xx <b>{counts["5xx"] || 0}</b></span></div>
            </article>
          </section>
          <section className="column">
            <article className="card orders-card">
              <div className="card-heading"><div><p className="eyebrow">This session</p><h2>Live orders</h2></div><span className="count-badge">{orders.length}</span></div>
              <div className="table-wrap" aria-live="polite">
                {orders.length ? <table><thead><tr><th>Time</th><th>Order</th><th>Status</th><th>Latency</th><th>Trace id</th></tr></thead><tbody>{orders.map((order) => <tr key={`${order.traceId}-${order.id}`} className={order.status === "failed" ? "failed-row" : ""}><td>{order.createdAt}</td><td><strong>#{order.id}</strong><small>{order.item} x{order.quantity}</small>{order.error && <small className="error-copy">{order.error}</small>}</td><td><span className={`order-status ${order.status}`}>{order.status}</span></td><td>{Math.round(order.latency)} ms</td><td><code>{order.traceId.slice(0, 10)}…</code><button className="icon-button" aria-label="Copy trace id" onClick={() => void copyTrace(order.traceId)}>Copy</button>{tempoBase && <a className="trace-link" href={`${tempoBase}/${order.traceId}`} target="_blank" rel="noreferrer">Open trace</a>}</td></tr>)}</tbody></table> : <div className="empty-state">No orders yet. Place one and its trace id appears here.</div>}
              </div>
            </article>
          </section>
        </div>
        <article className={`card tape-card ${tapeOpen ? "open" : "closed"}`}>
          <div className="card-heading"><div><p className="eyebrow">Browser to backend</p><h2>Telemetry tape</h2></div><button className="button secondary" onClick={() => setTapeOpen(!tapeOpen)}>{tapeOpen ? "Collapse tape" : "Open tape"}</button></div>
          {tapeOpen && <div className="tape" aria-live="polite">{tape.length ? tape.map((event, index) => <div className="tape-row" key={`${event.time}-${index}`}><time>{event.time}</time><span className={`kind ${event.kind}`}>{event.kind}</span><code>{event.name}</code><span>{event.detail}</span>{event.traceId && tempoBase && <a className="text-link" href={`${tempoBase}/${event.traceId}`} target="_blank" rel="noreferrer">Open trace</a>}</div>) : <div className="empty-state">Actions from this page appear here.</div>}</div>}
        </article>
      </main>
    </div>
  );
}

function Field({ label, name, type = "text", autoComplete, value, error, onChange }: { label: string; name: string; type?: string; autoComplete?: string; value: string; error?: string; onChange: (value: string) => void }) {
  const errorId = `${name}-error`;
  return <label className="field">{label}<input name={name} type={type} autoComplete={autoComplete} value={value} aria-invalid={Boolean(error)} aria-describedby={error ? errorId : undefined} onChange={(event) => onChange(event.target.value)} />{error && <span id={errorId} className="field-error" role="alert">{error}</span>}</label>;
}
