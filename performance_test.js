import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate, Counter } from "k6/metrics";

// ─── Custom metrics ───────────────────────────────────────────────
const loginDuration   = new Trend("login_duration",   true);
const productsDuration = new Trend("products_duration", true);
const cartDuration    = new Trend("cart_duration",    true);
const ordersDuration  = new Trend("orders_duration",  true);
const errorRate       = new Rate("error_rate");
const totalRequests   = new Counter("total_requests");

// ─── Test configuration ───────────────────────────────────────────
// Three scenarios run sequentially:
//   1. normal_load  — 10 concurrent users, 1 min
//   2. peak_load    — 50 concurrent users, 1 min
//   3. spike_load   — ramp to 100 users in 10 s, hold 30 s, ramp down
export const options = {
  scenarios: {
    normal_load: {
      executor: "constant-vus",
      vus: 10,
      duration: "1m",
      tags: { scenario: "normal" },
    },
    peak_load: {
      executor: "constant-vus",
      vus: 50,
      duration: "1m",
      startTime: "70s",        // starts after normal_load + 10 s gap
      tags: { scenario: "peak" },
    },
    spike_load: {
      executor: "ramping-vus",
      startTime: "140s",       // starts after peak_load + 10 s gap
      stages: [
        { duration: "10s", target: 100 },  // rapid ramp-up
        { duration: "30s", target: 100 },  // hold spike
        { duration: "10s", target: 0   },  // ramp-down
      ],
      tags: { scenario: "spike" },
    },
  },

  // Pass/Fail thresholds (these become your quality gates)
  thresholds: {
    http_req_duration:  ["p(95)<2000"],   // 95th percentile under 2 s
    http_req_failed:    ["rate<0.10"],    // error rate under 10 %
    login_duration:     ["p(95)<1500"],
    products_duration:  ["p(95)<1000"],
    cart_duration:      ["p(95)<1500"],
    orders_duration:    ["p(95)<2000"],
  },
};

const BASE = "http://localhost:8000";

// ─── Helper: login and return a bearer token ──────────────────────
function getToken() {
  const res = http.post(
    `${BASE}/api/auth/login/`,
    JSON.stringify({ email: "buyer1@test.com", password: "Test123!" }),
    { headers: { "Content-Type": "application/json" } }
  );
  if (res.status === 200) {
    return res.json("access");
  }
  return null;
}

// ─── Main virtual-user function ───────────────────────────────────
export default function () {
  // ── 1. Login ──────────────────────────────────────────────────
  const loginStart = Date.now();
  const loginRes = http.post(
    `${BASE}/api/auth/login/`,
    JSON.stringify({ email: "buyer1@test.com", password: "Test123!" }),
    { headers: { "Content-Type": "application/json" } }
  );
  loginDuration.add(Date.now() - loginStart);
  totalRequests.add(1);

  const loginOk = check(loginRes, {
    "login: status 200":       (r) => r.status === 200,
    "login: has access token": (r) => r.json("access") !== undefined,
  });
  errorRate.add(!loginOk);

  if (!loginOk) {
    sleep(1);
    return;
  }

  const token   = loginRes.json("access");
  const headers = {
    "Content-Type":  "application/json",
    "Authorization": `Bearer ${token}`,
  };

  sleep(0.5);

  // ── 2. Browse products ────────────────────────────────────────
  const prodStart = Date.now();
  const prodRes   = http.get(`${BASE}/api/products/`, { headers });
  productsDuration.add(Date.now() - prodStart);
  totalRequests.add(1);

  const prodOk = check(prodRes, {
    "products: status 200":   (r) => r.status === 200,
    "products: has results":  (r) => r.json("results") !== undefined || Array.isArray(r.json()),
  });
  errorRate.add(!prodOk);

  // Pick first product ID for cart (default to 1 if parse fails)
  let productId = 1;
  try {
    const body = prodRes.json();
    const list  = Array.isArray(body) ? body : body.results;
    if (list && list.length > 0) productId = list[0].id;
  } catch (_) {}

  sleep(0.5);

  // ── 3. Add item to cart ───────────────────────────────────────
  const cartStart = Date.now();
  const cartRes   = http.post(
    `${BASE}/api/cart/items/`,
    JSON.stringify({ product_id: productId, quantity: 1 }),
    { headers }
  );
  cartDuration.add(Date.now() - cartStart);
  totalRequests.add(1);

  const cartOk = check(cartRes, {
    "cart add: status 200 or 201": (r) => [200, 201].includes(r.status),
  });
  errorRate.add(!cartOk);

  sleep(0.5);

  // ── 4. Place order ────────────────────────────────────────────
  const orderStart = Date.now();
  const orderRes   = http.post(
    `${BASE}/api/orders/`,
    JSON.stringify({ shipping_address: "Test Street 1, Almaty" }),
    { headers }
  );
  ordersDuration.add(Date.now() - orderStart);
  totalRequests.add(1);

  const orderOk = check(orderRes, {
    "order: status 200 or 201": (r) => [200, 201].includes(r.status),
  });
  errorRate.add(!orderOk);

  sleep(1);
}

// ─── Summary report printed after the run ─────────────────────────
export function handleSummary(data) {
  const metrics = data.metrics;

  function p(metric, stat) {
    try { return Math.round(metrics[metric].values[stat]); }
    catch (_) { return "n/a"; }
  }

  const report = `
=============================================================
  ShopMarket — Performance Test Summary
=============================================================

  Endpoint         avg (ms)   med (ms)   p95 (ms)
  ─────────────────────────────────────────────────
  POST /auth/login    ${p("login_duration","avg")}       ${p("login_duration","med")}       ${p("login_duration","p(95)")}
  GET  /products/     ${p("products_duration","avg")}       ${p("products_duration","med")}       ${p("products_duration","p(95)")}
  POST /cart/items/   ${p("cart_duration","avg")}       ${p("cart_duration","med")}       ${p("cart_duration","p(95)")}
  POST /orders/       ${p("orders_duration","avg")}       ${p("orders_duration","med")}       ${p("orders_duration","p(95)")}

  Total requests : ${p("total_requests","count")}
  Error rate     : ${Math.round((metrics["error_rate"]?.values?.rate || 0) * 100)}%
  HTTP failures  : ${Math.round((metrics["http_req_failed"]?.values?.rate || 0) * 100)}%

  Thresholds
  ─────────────────────────────────────────────────
  p(95) overall < 2000 ms : ${metrics["http_req_duration"]?.values?.["p(95)"] < 2000 ? "PASS" : "FAIL"}
  error rate    < 10 %    : ${(metrics["error_rate"]?.values?.rate || 0) < 0.10 ? "PASS" : "FAIL"}
=============================================================
`;

  return {
    stdout: report,
    "performance_summary.txt": report,
  };
}
