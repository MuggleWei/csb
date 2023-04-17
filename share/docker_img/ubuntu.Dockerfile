ARG OS_VER
FROM ubuntu:${OS_VER}

ARG MIRROR
RUN if [ -n "$MIRROR" ]; then  \
		echo "use mirror $MIRROR"; \
		sed -i "s@archive.ubuntu.com@${MIRROR}@g" /etc/apt/sources.list; \
		sed -i "s@security.ubuntu.com@${MIRROR}@g" /etc/apt/sources.list; \
	fi
RUN apt-get update
RUN apt-get install -y ca-certificates
RUN sed -i "s@http@https@g" /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y build-essential
RUN apt-get install -y gdb
RUN apt-get install -y git
RUN apt-get install -y cmake
