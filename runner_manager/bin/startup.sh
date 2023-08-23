#!/usr/bin/env bash

# check if the script is being run inside a google cloud compute instance
# to perform this check we are looking for the metadata server
# if the metadata server is not found, we assume that the script is being run
# outside of a google cloud compute instance
if curl -s -f -m 5 -o /dev/null http://metadata.google.internal/computeMetadata/v1/instance/attributes/ -H "Metadata-Flavor: Google"; then
	# We are running inside a google cloud compute instance
	# Retrieving the metadata keys
	METADATA_KEYS=$(curl -s -f -m 5 http://metadata.google.internal/computeMetadata/v1/instance/attributes/ -H "Metadata-Flavor: Google")
	for key in ${METADATA_KEYS}; do
		# if the key starts with RUNNER_ then we export it as an environment variable
		if [[ ${key} =~ ^RUNNER_ ]]; then
			export "${key}"="$(curl -s -f -m 5 http://metadata.google.internal/computeMetadata/v1/instance/attributes/"${key}" -H 'Metadata-Flavor: Google')"
		fi
	done
fi

RUNNER_NAME=${RUNNER_NAME:-$(hostname)}
RUNNER_ORG=${RUNNER_ORG:-"org"}
RUNNER_LABELS=${RUNNER_LABELS:-"runner"}
RUNNER_TOKEN=${RUNNER_TOKEN:-"token"}
RUNNER_GROUP=${RUNNER_GROUP:-"default"}
RUNNER_WORKDIR=${RUNNER_WORKDIR:-"_work"}
RUNNER_DOWNLOAD_URL=${RUNNER_DOWNLOAD_URL:-"https://github.com/actions/runner/releases/download/v2.308.0/actions-runner-linux-x64-2.308.0.tar.gz"}
RUNNER_FILE=${RUNNER_FILE:-$(basename "${RUNNER_DOWNLOAD_URL}")}
LSB_RELEASE_CS=${LSB_RELEASE_CS:-$(lsb_release -cs))}

source /etc/os-release
LINUX_OS=${ID}
LINUX_OS_VERSION=$(echo "${VERSION_ID}" | sed -E 's/^([0-9]+)\..*$/\1/')
DOCKER_SERVICE_START="yes"

SSH_KEYS=${SSH_KEYS:-""}

sudo groupadd -f docker
sudo useradd -m actions
sudo usermod -aG docker,root actions
sudo bash -c "echo 'actions ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"
sudo -H -u actions bash -c 'mkdir -p /home/actions/.ssh'
sudo -H -u actions bash -c 'echo "${SSH_KEYS}" >>  /home/actions/.ssh/authorized_keys'

if [[ ${LINUX_OS} == "ubuntu" ]]; then
	sudo apt-get -y update
	sudo DEBIAN_FRONTEND=noninteractive apt-get -y install apt-transport-https \
		ca-certificates \
		curl \
		gnupg \
		lsb-release
elif [[ ${LINUX_OS} == "centos" ]] || [[ ${LINUX_OS} == "rocky" ]] || [[ ${LINUX_OS} == "almalinux" ]]; then
	sudo yum install -y bind-utils yum-utils
elif [[ ${LINUX_OS} == "rhel" ]]; then
	sudo bash -c 'cat <<EOF > /etc/systemd/system/redhat_registration.service
[Unit]
Description=Redhat registration
After=network-online.target

[Service]
Type=oneshot
RemainAfterExit=true
TimeoutStartSec=300
ExecStart=/sbin/subscription-manager register --username={{ redhat_username }} --password={{ redhat_password }} --auto-attach
TimeoutStopSec=300
ExecStop=-/sbin/subscription-manager unregister

[Install]
WantedBy=multi-user.target
EOF'
	sudo chmod 600 /etc/systemd/system/redhat_registration.service
	sudo systemctl daemon-reload
	sudo systemctl enable redhat_registration.service
	sudo systemctl start redhat_registration.service
else
	echo "OS not managed by the runner-manager"
	exit 1
fi

if [[ ! ${RUNNER_LABELS} =~ "no-docker" ]]; then

	if [[ ${LINUX_OS} == "ubuntu" ]]; then
		sudo install -m 0755 -d /etc/apt/keyrings
		sudo apt-get -y update
		curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
		sudo chmod a+r /etc/apt/keyrings/docker.gpg
		echo \
			"deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
			"$(. /etc/os-release && echo "${VERSION_CODENAME}")" stable" |
			sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
		sudo apt-get update --yes
		sudo apt-get install --yes docker-ce docker-ce-cli containerd.io
	elif [[ ${LINUX_OS} == "centos" ]] || [[ ${LINUX_OS} == "rocky" ]] || [[ ${LINUX_OS} == "almalinux" ]]; then
		sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
		sudo yum install -y epel-release docker-ce docker-ce-cli containerd.io
	elif [[ ${LINUX_OS} == "rhel" ]]; then
		if [[ ${LINUX_OS_VERSION} == "7" ]]; then
			# Enable repos to install docker
			sudo mkdir /etc/docker/
			# TODO: make dns config a setting for the runner
			sudo bash -c 'cat >  /etc/docker/daemon.json << EOF
            {
              "dns": ["10.100.1.1", "10.100.1.2", "10.100.1.3"]
            }
            EOF'

			sudo subscription-manager repos --enable=rhel-7-server-extras-rpms --enable=rhel-7-server-optional-rpms
			sudo yum install -y docker
		elif [[ ${LINUX_OS_VERSION} == "8" || ${LINUX_OS_VERSION} == "9" ]]; then
			sudo dnf install -y podman-docker podman
			DOCKER_SERVICE_START="no"
		else
			echo "RHEL version not managed by the runner-manager"
			exit 1
		fi
	fi

	if [[ ${DOCKER_SERVICE_START} == "yes" ]]; then
		sudo systemctl start docker
	fi
fi

# Login as actions user so that all the following commands are executed as actions user
mkdir -p /home/actions/actions-runner
cd /home/actions/actions-runner || exit
# Download the runner package
curl -L "${RUNNER_DOWNLOAD_URL}" -o "/tmp/${RUNNER_FILE}"
tar xzf /tmp/"${RUNNER_FILE}"
# install dependencies
sudo ./bin/installdependencies.sh
echo "[Unit]
Description={{Description}}
After=network.target

[Service]
ExecStart=/bin/bash {{RunnerRoot}}/runsvc.sh
User={{User}}
WorkingDirectory={{RunnerRoot}}
KillMode=process
KillSignal=SIGTERM
TimeoutStopSec=5min

[Install]
WantedBy=multi-user.target" >/home/actions/actions-runner/bin/actions.runner.service.template

sudo chown -Rh actions:actions /home/actions/actions-runner
sudo -u actions /home/actions/actions-runner/config.sh \
	--url "https://github.com/${RUNNER_ORG}" \
	--token "${RUNNER_TOKEN}" \
	--name "${RUNNER_NAME}" \
	--work "${RUNNER_WORKDIR}" \
	--labels "${RUNNER_LABELS}" \
	--runnergroup "${RUNNER_GROUP}" \
	--replace \
	--unattended \
	--ephemeral

if command -v systemctl; then
	sudo ./svc.sh install
	sudo ./svc.sh start
else
	nohup /home/actions/actions-runner/run.sh 2>/home/actions/actions-runner/logs &
fi
