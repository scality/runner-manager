import requests
import os
from pprint import PrettyPrinter

pprinter = PrettyPrinter()

HEADERS = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': f'token {os.getenv("GITHUB_TOKEN")}'
}


def link_download_runner(org, archi='x64'):
    return next(elem
                for elem in requests.get(f'https://api.github.com/orgs/{org}/actions/runners/downloads', headers=HEADERS).json()
                if elem['os'] == 'linux' and elem['architecture'] == archi)


def infos_runners(org):
    return requests.get(f'https://api.github.com/orgs/{org}/actions/runners', headers=HEADERS).json()


def list_runners(org):
    response = requests.get(f'https://api.github.com/orgs/{org}/actions/runners', headers=HEADERS)
    pprinter.pprint(response.json())
    return response.json()


def create_runner_token(org):
    """
    Create  a token used as paramert of the github action script start, this token is available one hour.
    `./config.sh --url URL --token TOKEN`
    :return:
    """
    response = requests.post(f'https://api.github.com/orgs/{org}/actions/runners/registration-token', headers=HEADERS).json()

    pprinter.pprint(response)
    return response['token']


def remove_runner_token(org, runner_id):
    """
    Create  a token used as paramert of the github action script start, this token is available one hour.
    `./config.sh remove --token TOKEN`
    :return:
    """
    response = requests.post(f'https://api.github.com/orgs/{org}/actions/runners/{runner_id}', headers=HEADERS).json()

    pprinter.pprint(response)
    return response['token']


def force_delete_runner(org, runner_id):
    """
    :return:
    """
    response = requests.delete(f'https://api.github.com/orgs/{org}/actions/runners/{runner_id}', headers=HEADERS)
    if response.status_code != 204:
        raise Exception("Error in response")