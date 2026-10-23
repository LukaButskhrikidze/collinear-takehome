# Same interpreter and packages as my pipeline's environment.
FROM python:3.9.25-slim

# curl: opencode's installer needs it (Harbor installs opencode during setup)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir gemmi==0.7.5 numpy==2.0.2 scipy==1.13.1 PyYAML==6.0.3

# without this opencode cuts every response at 32k tokens (brief 2.6)
ENV OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX=64000

WORKDIR /app
COPY data /app/data
