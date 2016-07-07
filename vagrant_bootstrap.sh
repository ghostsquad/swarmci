#!/bin/bash

sudo yum install epel-release
sudo yum update -y
sudo yum install python34
sudo easy_install pip
sudo curl -fsSL https://test.docker.com/ | sh
sudo usermod -aG docker vagrant

mkdir -p /tmp

cat >/tmp/docker.service <<EOF
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network.target docker.socket
Requires=docker.socket

[Service]
Type=notify
# the default is not to use systemd for cgroups because the delegate issues still
# exists and systemd currently does not support the cgroup feature set required
# for containers run by docker
ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock
ExecReload=/bin/kill -s HUP $MAINPID
LimitNOFILE=1048576
LimitNPROC=1048576
LimitCORE=infinity
# Uncomment TasksMax if your systemd version supports it.
# Only systemd 226 and above support this version.
#TasksMax=infinity
TimeoutStartSec=0
# set delegate yes so that systemd does not reset the cgroups of docker containers
Delegate=yes
# kill only the docker process, not all processes in the cgroup
KillMode=process

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/docker.service  /etc/systemd/system/docker.service

sudo rm -f /etc/docker/key.json

sudo systemctl daemon-reload
sudo systemctl enable docker.service
sudo systemctl start docker.service

sleep 3

if [ `cat /etc/hostname` == "manager" ]; then
    sudo yum install -y epel-release
    sudo yum install -y python34
    curl -O https://bootstrap.pypa.io/get-pip.py
    sudo /usr/bin/python3.4 get-pip.py

    docker run -d -p 8500:8500 --name=consul --restart=always progrium/consul -server -bootstrap
    docker run -d -p 4000:4000 swarm manage -H :4000 --replication --advertise 172.85.0.100:4000 consul://172.85.0.100:8500
elif [ `cat /etc/hostname` == "node1" ]; then
    docker run -d swarm join --advertise=172.85.0.101:2375 consul://172.85.0.100:8500
else
    docker run -d swarm join --advertise=172.85.0.102:2375 consul://172.85.0.100:8500
fi

#docker -H :4000 info

# to test that everything is working, the prior command should show 2 healthy nodes
# deploy a lightweight container to every node with (run twice):
# docker -H :4000 run -d -p 80:80 nginx:alpine