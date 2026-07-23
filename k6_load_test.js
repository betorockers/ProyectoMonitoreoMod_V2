import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '5s', target: 20 }, // Ramp-up to 20 users
    { duration: '10s', target: 20 }, // Stay at 20 users
    { duration: '5s', target: 0 },  // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.01'],   // Error rate must be less than 1%
  },
};

export default function () {
  const BASE_URL = 'http://127.0.0.1:8000';

  // 1. Health check
  const resStatus = http.get(`${BASE_URL}/api/v1/system/status`);
  check(resStatus, {
    'status is 200': (r) => r.status === 200,
    'has setup_complete': (r) => r.json().hasOwnProperty('setup_complete'),
  });

  // 2. Snapshot
  const resSnapshot = http.get(`${BASE_URL}/api/v1/snapshot`);
  check(resSnapshot, {
    'snapshot is 200': (r) => r.status === 200,
  });

  sleep(1);
}
