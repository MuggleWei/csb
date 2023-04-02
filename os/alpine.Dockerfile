ARG OS_VER
FROM alpine:${OS_VER}

ARG MIRROR
RUN if [ -n "$MIRROR" ]; then \
		echo "use mirror $MIRROR"; \
		sed -i "s/dl-cdn.alpinelinux.org/$MIRROR/g" /etc/apk/repositories; \
	fi
RUN apk update
RUN apk add --no-cache build-base
RUN apk add --no-cache gdb
RUN apk add --no-cache git
RUN apk add --no-cache cmake
