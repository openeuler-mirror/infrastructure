FROM golang:1.12.1-alpine3.9 AS builder

COPY . /go/src/gitee.com/openeuler/ci-bot

RUN apk --no-cache update && \
apk --no-cache upgrade && \
CGO_ENABLED=1 go build -v -o /usr/local/bin/ci-bot -ldflags="-w -s -extldflags -static" \
gitee.com/openeuler/ci-bot/cmd/cibot

RUN mkdir -p /bot

WORKDIR /bot

EXPOSE 8888

ENTRYPOINT ["ci-bot"]
