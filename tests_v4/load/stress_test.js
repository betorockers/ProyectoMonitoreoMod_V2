import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '5s', target: 20 },
    { duration: '10s', target: 50 },
    { duration: '5s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'], // menos del 1% de fallos
    http_req_duration: ['p(95)<500'], // 95% de las peticiones por debajo de 500ms
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://127.0.0.1:8000';

export default function () {
  const resDashboard = http.get(`${BASE_URL}/`);
  check(resDashboard, {
    'Dashboard status is 200': (r) => r.status === 200,
    'Dashboard body contains ARGOS': (r) => r.body.includes('ARGOS GUARD'),
  });

  const resHwid = http.get(`${BASE_URL}/licensing/info/`);
  check(resHwid, {
    'Licensing info status is 200': (r) => r.status === 200,
    'Licensing returns JSON': (r) => r.json().tier === 'ENTERPRISE AIR-GAPPED',
  });

  sleep(0.5);
}
