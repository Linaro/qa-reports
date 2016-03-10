# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|

  config.vm.box = "ubuntu/trusty64"
  config.vm.hostname = "qa-reports.linaro.org"

  config.vm.provider "virtualbox" do |v|
    v.memory = 2048
    v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    v.customize ["modifyvm", :id, "--natdnsproxy1", "on"]

    config.vm.network "private_network", ip:  "10.0.100.100"
    config.vm.synced_folder ".", "/vagrant", type: "nfs"
  end

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "ansible/site.yml"
    ansible.verbose = "vvvv"
  end

  config.ssh.forward_agent = true
end
