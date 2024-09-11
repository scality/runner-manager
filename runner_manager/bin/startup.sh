#!/usr/bin/env bash

NAME="${RUNNER_NAME}"
LABELS="${RUNNER_LABELS}"
JIT_CONFIG="${RUNNER_JIT_CONFIG}"
REDHAT_USERNAME="${RUNNER_REDHAT_USERNAME}"
REDHAT_PASSWORD="${RUNNER_REDHAT_PASSWORD}"
DOWNLOAD_URL="${RUNNER_DOWNLOAD_URL}"
FILE=${FILE:-$(basename "${DOWNLOAD_URL}")}

source /etc/os-release
LINUX_OS=${ID}
LINUX_OS_VERSION=$(echo "${VERSION_ID}" | sed -E 's/^([0-9]+)\..*$/\1/')
DOCKER_SERVICE_START="yes"

SSH_KEYS=${SSH_KEYS:-""}

SCRIPT_FILE=$(readlink -f "$0")

function setup_runner_hook {
	mkdir -p /opt/runner
	# Ensure this script exists even after cloud-init
	cp "${SCRIPT_FILE}" /opt/runner/startup.sh
	# setup the content of the function job_started in the file /opt/runner/started.sh
	echo "#!/usr/bin/env bash
/opt/runner/startup.sh --job-started" | sudo tee /opt/runner/started.sh
	chmod +x /opt/runner/started.sh
	# same for job_completed
	echo "#!/usr/bin/env bash
/opt/runner/startup.sh --job-completed" | sudo tee /opt/runner/completed.sh
	chmod +x /opt/runner/completed.sh
	# Ensure the user actions can execute the hooks
	sudo chown -R actions:actions /opt/runner
	touch /home/actions/actions-runner/.env
	echo "ACTIONS_RUNNER_HOOK_JOB_STARTED=/opt/runner/started.sh" >>/home/actions/actions-runner/.env
	echo "ACTIONS_RUNNER_HOOK_JOB_COMPLETED=/opt/runner/completed.sh" >>/home/actions/actions-runner/.env
	chown actions:actions /home/actions/actions-runner/.env

}

function job_started {
	# This function is called before the job starts
	echo "Running preliminary checks..."
	# Check if apt, dnf, or yum is running
	echo "Ensure no package manager is running"
	local tries=0
	while pgrep -x "apt" >/dev/null || pgrep -x "dnf" >/dev/null || pgrep -x "yum" >/dev/null; do
		echo "Waiting for package manager to finish"
		((tries++))
		sleep "${tries}"
		if [[ ${tries} -eq 10 ]]; then
			echo "::warning::Package manager did not finish"
			break
		fi
	done

	# reset tries counter
	tries=0
	if [[ ! ${LABELS} =~ "no-docker" ]]; then
		echo "Ensure docker is running"
		while ! docker info >/dev/null 2>&1; do
			echo "Waiting for docker to start"
			((tries++))
			sleep "${tries}"
			if [[ ${tries} -eq 10 ]]; then
				echo "::warning::Docker did not start"
				break
			fi
		done
	fi
	# Run bash injected through runner group config
	bash /opt/runner/job_started_script.sh
	echo "Done"
}

function job_completed {
	# This function is called when the job is completed
	# Run bash injected through runner group config
	bash /opt/runner/job_completed_script.sh
	echo "Job completed"

}

function setup_service {
	# When running the runner as a just-in-time runner, the runsvc.sh script
	# is not created. Therefore we are manually creating it here.

	echo "[Unit]
Description=GitHub Actions Runner
After=network.target

[Service]
ExecStart=/bin/bash /home/actions/actions-runner/run.sh --jitconfig \"${JIT_CONFIG}\"
User=actions
WorkingDirectory=/home/actions/actions-runner
KillMode=process
KillSignal=SIGTERM
TimeoutStopSec=5min

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/actions.runner.service

	sudo systemctl daemon-reload
	sudo chown -Rh actions:actions /home/actions/actions-runner

}

function setup_hostname {
	# Ensure the hostname is defined in /etc/hosts
	local hostname
	hostname=$(hostname)

	# Check if the hostname is in /etc/hosts
	if ! grep -q "${hostname}" /etc/hosts; then
		# If it's not in the file, append it
		echo "127.0.0.1 ${hostname}" | sudo tee -a /etc/hosts
	fi
}

function setup_runner {
	sudo groupadd -f docker
	sudo useradd -m actions
	sudo usermod -aG docker,root actions
	sudo bash -c "echo 'actions ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"
	sudo -H -u actions bash -c 'mkdir -p /home/actions/.ssh'
	sudo -H -u actions bash -c 'echo "${SSH_KEYS}" >>  /home/actions/.ssh/authorized_keys'

	# Login as actions user so that all the following commands are executed as actions user
	mkdir -p /home/actions/actions-runner
	cd /home/actions/actions-runner || exit
	# Download the runner package
	curl -L "${DOWNLOAD_URL}" -o "/tmp/${FILE}"
	tar xzf /tmp/"${FILE}"
	# install dependencies
	sudo ./bin/installdependencies.sh

	setup_runner_hook
	# check if systemctl is available
	if [[ -x "$(command -v systemctl)" ]]; then
		setup_service
		sudo systemctl enable actions.runner.service
		sudo systemctl start actions.runner.service
	else
		sudo -H -u actions bash -c "nohup /home/actions/actions-runner/run.sh --jitconfig \"${JIT_CONFIG}\" 2>/home/actions/actions-runner/logs &"
	fi

	cat <<EOF >/opt/runner/job_started_script.sh
${RUNNER_JOB_STARTED_SCRIPT}
EOF

	cat <<EOF >/opt/runner/job_completed_script.sh
${RUNNER_JOB_COMPLETED_SCRIPT}
EOF

}

function install_docker {

	if [[ ! ${LABELS} =~ "no-docker" ]]; then

		if [[ ${LINUX_OS} == "ubuntu" ]] || [[ ${LINUX_OS} == "debian" ]]; then
			sudo install -m 0755 -d /etc/apt/keyrings
			sudo apt-get -y update
			curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
			sudo chmod a+r /etc/apt/keyrings/docker.gpg
			echo \
				deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
				"$(. /etc/os-release && echo "${VERSION_CODENAME}")" stable |
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
}

function init {
	if [[ ${LINUX_OS} == "ubuntu" ]] || [[ ${LINUX_OS} == "debian" ]]; then
		sudo apt-get -y update
		sudo DEBIAN_FRONTEND=noninteractive apt-get -y install apt-transport-https \
			ca-certificates \
			curl \
			gnupg \
			lsb-release
	elif [[ ${LINUX_OS} == "centos" ]] || [[ ${LINUX_OS} == "rocky" ]] || [[ ${LINUX_OS} == "almalinux" ]]; then
		if [[ ${LINUX_OS_VERSION} == "7" ]]; then
			# CentOS 7 is EOL and mirrorlist does no longer exists
			# using another mirror as a temporary workaround
			sed -i 's/^mirrorlist=/#mirrorlist=/; s/^#baseurl=/baseurl=/; s/mirror\.centos\.org/vault\.centos\.org/' /etc/yum.repos.d/*.repo
		fi
		sudo yum install -y bind-utils yum-utils
	elif [[ ${LINUX_OS} == "rhel" ]]; then
		echo "
[Unit]
Description=Redhat registration
After=network-online.target

[Service]
Type=oneshot
RemainAfterExit=true
TimeoutStartSec=300
ExecStart=/sbin/subscription-manager register --username=${REDHAT_USERNAME} --password=${REDHAT_PASSWORD} --auto-attach
TimeoutStopSec=300
ExecStop=-/sbin/subscription-manager unregister

[Install]
WantedBy=multi-user.target
" | sudo tee /etc/systemd/system/redhat_registration.service
		sudo chmod 600 /etc/systemd/system/redhat_registration.service
		sudo systemctl daemon-reload
		sudo systemctl enable redhat_registration.service
		sudo systemctl start redhat_registration.service
	else
		echo "OS not managed by the runner-manager"
		exit 1
	fi
}

# Retrieve the args passed to the script
# If script is triggered by a hook, call the corresponding function
while [[ $# -gt 0 ]]; do
	case "$1" in
	--job-started)
		job_started
		exit 0
		;;
	--job-completed)
		job_completed
		exit 0
		;;
	*)
		echo "Unknown argument: $1"
		exit 1
		;;
	esac
done

init
install_docker
setup_hostname
setup_runner
