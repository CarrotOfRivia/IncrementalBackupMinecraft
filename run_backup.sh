#!/bin/bash

cd "$(dirname "$0")"

export PYTHONPATH=./:PYTHONPATH
/home/carrot_of_rivia/miniconda3/envs/gmail/bin/python run_backup.py