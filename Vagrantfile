# -*- mode: ruby -*-
# vi: set ft=ruby :
# Specify Vagrant version and Vagrant API version
Vagrant.require_version ">= 1.6.0"
VAGRANTFILE_API_VERSION = "2"

# run this first:
# vagrant plugin install vagrant-vbguest
# vagrant plugin install vagrant-hostmanager

# Create and configure the VM(s)
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.box = "williamyeh/centos7-docker"

    # Skip checking for an updated Vagrant box
    config.vm.box_check_update = false

    config.vbguest.auto_update = false

    config.hostmanager.enabled = true
    config.hostmanager.manage_host = true
    config.hostmanager.manage_guest = true
    config.hostmanager.ignore_private_ip = false
    config.hostmanager.include_offline = true

    # Don't use Vagrant's default insecure key
    config.ssh.insert_key = false

    config.vm.provision "shell", path: "vagrant_bootstrap.sh"

    config.vm.provider "virtualbox" do |v|
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
        v.memory = 2048
        v.cpus = 2
    end

    config.vm.define "manager" do |node|
        node.vm.hostname = "manager"
        node.vm.network :private_network, ip: "172.85.0.100"
    end

    config.vm.define "node1" do |node|
        node.vm.hostname = "node1"
        node.vm.network :private_network, ip: "172.85.0.101"
    end

    config.vm.define "node2" do |node|
        node.vm.hostname = "node2"
        node.vm.network :private_network, ip: "172.85.0.102"
    end
end
