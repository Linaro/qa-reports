# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|

  config.vm.box = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
  config.vm.hostname = "qa-reports.linaro.org"
  config.vm.network "private_network", ip:  "10.0.100.100"

  config.vm.provider "virtualbox" do |v|
    v.memory = 2048
    v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    v.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
  end

  config.vm.synced_folder ".", "/vagrant", type: "nfs"

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "ansible/site.yml"
    ansible.verbose = "vvvv"
  end
  
  config.ssh.forward_agent = true
end
