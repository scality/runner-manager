from githubkit.webhooks.types import WebhookEvent


def handle_webhook(webhook: WebhookEvent):
    print(webhook)
