#!/usr/bin/env bash
{% if 'ubuntu'  in image %}
sudo apt-get update
sudo apt-get install apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
   lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update --yes --force-yes
sudo apt-get install --yes --force-yes docker-ce docker-ce-cli containerd.io
{% elif 'centos' in image %}
sudo yum install -y bind-utils yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y epel-release docker-ce docker-ce-cli containerd.io
{% else %}
echo "OS not managed by the runner-manager"
exit 1
{% endif %}

sudo systemctl start docker

sudo useradd -m  actions
sudo usermod -aG docker,root actions
sudo bash -c "echo 'actions ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"

sudo -H -u actions bash -c 'cd /home/actions/ && mkdir actions-runner && cd actions-runner && curl -O -L {{ installer["download_url"] }} && tar xzf ./{{ installer["filename"] }}'
sudo -H -u actions bash -c 'sudo /home/actions/actions-runner/bin/installdependencies.sh'
sudo -H -u actions bash -c '/home/actions/actions-runner/config.sh --url https://github.com/{{ github_organization }} --token {{ token }} --name {{ name }} --work _work  --labels {{ tags }} --runnergroup {{ group }}'
nohup sudo -H -u actions bash -c '/home/actions/actions-runner/run.sh --once 2> /home/actions/actions-runner/logs'
