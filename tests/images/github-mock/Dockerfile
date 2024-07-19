FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PRISM_VERSION=v5.3.1

RUN curl https://github.com/stoplightio/prism/releases/download/${PRISM_VERSION}/prism-cli-linux \
    -L \
    -o /usr/local/bin/prism \
    && chmod +x /usr/local/bin/prism

WORKDIR /app

RUN curl -O -L https://raw.githubusercontent.com/github/rest-api-description/a2f6c1ddb1840778cf7a4119c4446d697f77500e/descriptions/ghec/ghec.2022-11-28.json

# There's a misconfiguration in the openapi file, we are going to replace the following strings:
# - "server-statistics-actions.yaml" -> "#/components/schemas/server-statistics-actions"
# - "server-statistics-packages.yaml" -> "#/components/schemas/server-statistics-packages"

RUN sed -i 's/server-statistics-actions.yaml/#\/components\/schemas\/server-statistics-actions/g' ghec.2022-11-28.json \
    && sed -i 's/server-statistics-packages.yaml/#\/components\/schemas\/server-statistics-packages/g' ghec.2022-11-28.json

ENTRYPOINT [ "prism" ]

CMD ["mock", "ghec.2022-11-28.json", "-h", "0.0.0.0"]
