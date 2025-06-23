from logging import INFO

from decouple import config

config.search_path = "./docker"


DEBUG=False
LOGGER_LEVEL= INFO

if config("DEBUG"):
    DEBUG=config("DEBUG")
    LOGGER_LEVEL=10

JIRA_SERVER = config("JIRA_SERVER")
JIRA_TOKEN = config("JIRA_TOKEN")

LIST_OF_AUTHORS = config("LIST_OF_AUTHORS")
