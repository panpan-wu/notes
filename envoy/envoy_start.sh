#!/bin/bash

exec /usr/bin/envoy -c /etc/envoy/envoy.yaml --restart-epoch $RESTART_EPOCH
