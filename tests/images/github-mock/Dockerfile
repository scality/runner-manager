FROM ghcr.io/stoplightio/prism/prism:master

HEALTHCHECK NONE

USER node

EXPOSE 4010

CMD ["mock", "https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/ghec/ghec.2022-11-28.json", "-h", "0.0.0.0"]