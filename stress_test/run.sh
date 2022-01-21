#!/bin/bash

go run main.go > results.bin
cat results.bin | vegeta report
