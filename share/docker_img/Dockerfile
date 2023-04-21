ARG REGISTRY
ARG OS
ARG OS_VER
FROM "${REGISTRY}/${REGISTRY}_${OS}:${OS_VER}" as builder

ARG FILENAME
RUN mkdir -p /app/src/
COPY ${FILENAME} /app/src/
RUN hpb build -c /app/src/${FILENAME}
