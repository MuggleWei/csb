ARG REGISTRY
ARG OS
ARG OS_VER
FROM "${REGISTRY}/${OS}:${OS_VER}" as builder

ARG REGISTRY
ARG OS
ARG OS_VER
ARG SOURCE_PATH
ARG BUILD_TYPE
ARG PKG_NAME

RUN mkdir -p /app/src/
COPY ${SOURCE_PATH} /app/src/mugglec
RUN mkdir -p /app/src/mugglec/build
RUN mkdir -p /app/src/mugglec/usr
RUN cmake \
	-S /app/src/mugglec \
	-B /app/src/mugglec/build \
	-DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
	-DCMAKE_INSTALL_PREFIX=/app/src/mugglec/usr \
	-DBUILD_SHARED_LIBS=ON
RUN cmake --build /app/src/mugglec/build --target install

WORKDIR /app/src/mugglec/usr
RUN mkdir -p /pkg
RUN tar -czvf ${PKG_NAME}.tar.gz ./*
RUN mv ${PKG_NAME}.tar.gz /pkg
