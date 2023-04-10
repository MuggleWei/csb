ARG REGISTRY
ARG OS
ARG OS_VER
FROM "${REGISTRY}/${OS}:${OS_VER}" as builder

ARG REGISTRY
ARG OS
ARG OS_VER
ARG SOURCE_DIR
ARG GIT_TAG
ARG BUILD_TYPE

RUN mkdir -p /app/src/
COPY ${SOURCE_DIR}/googletest /app/src/googletest
RUN mkdir -p /app/src/googletest/build
RUN cmake \
	-S /app/src/googletest \
	-B /app/src/googletest/build \
	-DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
	-DCMAKE_INSTALL_PREFIX=/opt/googletest \
	-DBUILD_SHARED_LIBS=ON
RUN cmake --build /app/src/googletest/build --target install

WORKDIR /opt/googletest
RUN mkdir -p /pkg
RUN tar -czvf googletest-${GIT_TAG}-${BUILD_TYPE}-${OS}${OS_VER}.tar.gz ./*
RUN mv googletest-${GIT_TAG}-${BUILD_TYPE}-${OS}${OS_VER}.tar.gz /pkg/
