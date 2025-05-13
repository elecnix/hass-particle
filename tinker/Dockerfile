ARG BUILD_FROM
FROM $BUILD_FROM

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY run.sh /
COPY daemon.py /
COPY .python-version /
COPY pyproject.toml /

RUN uv sync \
    && chmod a+x /run.sh

CMD [ "uv", "run", "/run.sh" ]
