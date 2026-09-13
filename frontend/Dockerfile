# syntax=docker/dockerfile:1

FROM nginx:1.29-alpine

RUN addgroup -S -g 10001 appgroup \
    && adduser -S -D -H -u 10001 -G appgroup appuser \
    && mkdir -p /var/cache/nginx \
    && mkdir -p /var/log/nginx \
    && mkdir -p /var/run \
    && chown -R appuser:appgroup \
        /var/cache/nginx \
        /var/log/nginx \
        /var/run \
        /usr/share/nginx/html \
        /etc/nginx/conf.d

COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/nginx.conf /etc/nginx/nginx.conf

RUN chown appuser:appgroup /usr/share/nginx/html/index.html \
    && chown appuser:appgroup /etc/nginx/nginx.conf

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
