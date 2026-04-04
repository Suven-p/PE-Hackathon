docker run --rm --env-file .env -v ./:/home/k6/k6 grafana/k6:1.7.1 run --out influxdb=http://host.docker.internal:8086/k6db --summary-mode=full k6/script.js
