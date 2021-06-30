import logging
import requests
from runners_manager.vm_creation.Exception import APIException

logger = logging.getLogger("runner_manager")


class GithubManager(object):
    organization: str
    headers: dict

    def __init__(self, organization, token):
        self.organization = organization
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {token}'
        }

    def link_download_runner(self, archi='x64'):
        download_link = f'https://api.github.com/orgs/{self.organization}/actions/runners/downloads'
        return next(
            elem
            for elem in requests.get(download_link, headers=self.headers).json()
            if elem['os'] == 'linux' and elem['architecture'] == archi
        )

    def get_runners(self):
        info_link = f'https://api.github.com/orgs/{self.organization}/actions/runners'
        return requests.get(info_link, headers=self.headers).json()

    def create_runner_token(self):
        """
        Create  a token used as paramert of the github action script start,
        this token is available one hour.
        `./config.sh --url URL --token TOKEN`
        :return:
        """
        token_link = \
            f'https://api.github.com/orgs/{self.organization}/actions/runners/registration-token'
        response = requests.post(token_link, headers=self.headers).json()

        return response['token']

    def force_delete_runner(self, runner_id: int):
        runner_link = f'https://api.github.com/orgs/{self.organization}/actions/runners/{runner_id}'
        response = requests.delete(runner_link, headers=self.headers)

        if response.status_code != 204:
            logger.error(f"Error in response: {response.status_code} {response.json()['message']}")
            raise APIException("Error in response")
