#!/bin/sh

gh extension install cli/gh-webhook

gh webhook forward  --repo="${REPO}" --events="${EVENTS}" --url="${URL}"
