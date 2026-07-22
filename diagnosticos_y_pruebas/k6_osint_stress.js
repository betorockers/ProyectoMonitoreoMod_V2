import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '5s', target: 20 }, // Rampa de subida a 20 usuarios
    { duration: '10s', target: 20 }, // Mantener 20 usuarios por 10s
    { duration: '5s', target: 0 },  // Rampa de bajada
  ],
};

const BASE_URL = 'http://127.0.0.1:8000';

export default function () {
  // Simularemos peticiones a los endpoints OSINT que no consumen APIs pesadas o son estáticos (para no bloquearnos)
  // Geografía
  let res1 = http.get(`${BASE_URL}/osint/geografia/?city=Santiago`);
  check(res1, { 'Geografía 200': (r) => r.status === 200 });

  // Web
  let res2 = http.get(`${BASE_URL}/osint/web/?url=betograf.cl`);
  check(res2, { 'Web 200': (r) => r.status === 200 });
  
  // Tactical Map View
  let res3 = http.get(`${BASE_URL}/partial/map/`);
  check(res3, { 'Mapa Táctico 200': (r) => r.status === 200 });

  sleep(1);
}
