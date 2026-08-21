import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// ============================================================
// CONFIG
// ============================================================

const BASE_URL = 'http://smartretailx-alb-2036217170.ap-south-1.elb.amazonaws.com/api/v1';

const TEST_EMAIL = 'testuser@example.com';
const TEST_PASSWORD = 'TestPass123!';

// ============================================================
// CUSTOM METRICS
// ============================================================

const loginFailureRate = new Rate('login_failures');
const productFailureRate = new Rate('product_failures');
const orderFailureRate = new Rate('order_failures');

const loginDuration = new Trend('login_duration');
const productDuration = new Trend('product_list_duration');
const orderDuration = new Trend('order_create_duration');

// ============================================================
// LOAD PROFILE
// ============================================================
// Ramps from 0 to 20 concurrent virtual users over 30s,
// holds 20 VUs for 1 minute, then ramps back down.
// Adjust stages to match what your report needs to demonstrate.

export const options = {
  stages: [
    { duration: '30s', target: 20 },  // ramp-up
    { duration: '1m', target: 20 },   // sustained load
    { duration: '20s', target: 50 },  // stress spike
    { duration: '20s', target: 0 },   // ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],   // 95% of requests under 2s
    http_req_failed: ['rate<0.05'],      // less than 5% error rate
    login_failures: ['rate<0.05'],
    product_failures: ['rate<0.05'],
  },
};

// ============================================================
// MAIN SCENARIO
// ============================================================

export default function () {

  // --------------------------------------------------------
  // 1. LOGIN
  // --------------------------------------------------------

  const loginPayload = JSON.stringify({
    email: TEST_EMAIL,
    password: TEST_PASSWORD,
  });

  const loginRes = http.post(`${BASE_URL}/users/login`, loginPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  loginDuration.add(loginRes.timings.duration);

  const loginOk = check(loginRes, {
    'login status is 200': (r) => r.status === 200,
    'login returns access_token': (r) => {
      try {
        return JSON.parse(r.body).access_token !== undefined;
      } catch {
        return false;
      }
    },
  });

  loginFailureRate.add(!loginOk);

  if (!loginOk) {
    sleep(1);
    return;
  }

  const accessToken = JSON.parse(loginRes.body).access_token;

  const authHeaders = {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
  };

  sleep(1);

  // --------------------------------------------------------
  // 2. BROWSE PRODUCTS
  // --------------------------------------------------------

  const productsRes = http.get(`${BASE_URL}/products`, authHeaders);

  productDuration.add(productsRes.timings.duration);

  const productsOk = check(productsRes, {
    'products status is 200': (r) => r.status === 200,
    'products returns array': (r) => {
      try {
        return Array.isArray(JSON.parse(r.body));
      } catch {
        return false;
      }
    },
  });

  productFailureRate.add(!productsOk);

  sleep(1);

  // --------------------------------------------------------
  // 3. GET OWN ORDERS
  // --------------------------------------------------------

  const ordersRes = http.get(`${BASE_URL}/orders`, authHeaders);

  check(ordersRes, {
    'orders status is 200': (r) => r.status === 200,
  });

  sleep(1);

  // --------------------------------------------------------
  // 4. HEALTH CHECK (lightweight, no auth)
  // --------------------------------------------------------

  const healthRes = http.get(`${BASE_URL}/health`);

  check(healthRes, {
    'gateway health is 200': (r) => r.status === 200,
  });

  sleep(1);
}
