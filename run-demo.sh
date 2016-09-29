#!/bin/bash
python3 /opt/swarmci/setup.py install --force
pushd /opt/swarmci
python3 -m swarmci
popd
