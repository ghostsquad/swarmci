#!/bin/bash
python3 /opt/swarmci/setup.py install --force
pushd /opt/swarmci
echo ""
echo "========== RUNNING SUCCESS DEMO =============="
echo ""
python3 -m swarmci
echo ""
echo "========== RUNNING FAILURE DEMO =============="
echo ""
python3 -m swarmci --file .swarmci.fails --debug
popd
