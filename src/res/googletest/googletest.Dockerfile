ARG REGISTRY
ARG OS
FROM "${REGISTRY}/${OS}" as builder

ARG GIT_REPO
ARG GIT_TAG
RUN mkdir -p /app/src/
RUN git clone --depth=1 --branch=${GIT_TAG} ${GIT_REPO} /app/src/googletest
RUN mkdir -p /app/src/googletest/build
RUN cmake \
	-S /app/src/googletest \
	-B /app/src/googletest/build \
	-DCMAKE_BUILD_TYPE=Release \
	-DCMAKE_INSTALL_PREFIX=/opt/googletest \
	-DBUILD_SHARED_LIBS=ON
RUN cmake --build /app/src/googletest/build --target install

WORKDIR /opt/googletest
RUN tar -czvf googletest-${GIT_TAG}.tar.gz ./*
