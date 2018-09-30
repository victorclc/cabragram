#!/usr/bin/env bash

function status {
    if [ ! -z `ps -ef | awk '$8=="python3.6" && $9=="cabra.py" {print $2}'` ]; then
        echo "A cabra esta rodando."
        exit 0
    else
        echo "A cabra esta parada."
        exit 1
    fi
}

status