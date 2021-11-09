"""Global class to handle all Prometheus metrics."""

from prometheus_client import Enum


class Metrics(object):
    runner_status = Enum(
        'openstack_actions_runner_status', 'Metrics displaying the status of a runner',
        states=['creating', 'deleting', 'respawning', 'online', 'running', 'offline'],
        labelnames=['name', 'flavor', 'image'],
    )
