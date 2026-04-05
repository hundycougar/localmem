FROM python:3.13-slim AS build

WORKDIR /app
COPY pyproject.toml .
COPY localmem/ localmem/

RUN pip install --no-cache-dir --prefix=/install .


FROM python:3.13-slim

RUN groupadd --gid 1000 localmem \
    && useradd --uid 1000 --gid 1000 --no-create-home localmem

COPY --from=build /install /usr/local

USER localmem
EXPOSE 8080

ENTRYPOINT ["localmem"]
CMD ["serve", "--host", "0.0.0.0"]
