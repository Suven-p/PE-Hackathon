import http from "k6/http";
import exec, { scenario } from 'k6/execution';
import { check, sleep } from "k6";
import { SharedArray } from 'k6/data';

const BASE_URL = __ENV.BASE_URL;
const data = new SharedArray('data', function () {
  const file = open('./urls.csv');
  return file.split('\n').slice(1).map(line => {
    const [short_url, long_url] = line.split(',');
    return { short_url, long_url };
  });
});

export const options = {
  vus: 500,
  iterations: 2000,
};

export function setup() {
  let res = http.get(`${BASE_URL}/health`);
  if (res.status !== 200) {
    exec.test.abort(`Got unexpected status code ${res.status} when trying to setup. Exiting.`);
  }
}

export default function () {
  let res = http.get(`${BASE_URL}/health`);
  // Get status value from json body
  let body = JSON.parse(res.body);
  check(res, { "status is 200": (res) => res.status === 200 && body.status === "ok" });

  let index = scenario.iterationInTest % data.length;
  let { short_url, long_url } = data[index];

  res = http.get(`${BASE_URL}/${short_url}`, {
    redirects: 0
  });
  check(res, { "redirects to long URL": (res) => res.status === 302 && res.headers.Location === long_url });
}
