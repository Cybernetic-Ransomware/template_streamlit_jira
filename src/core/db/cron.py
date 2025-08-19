from src.config.conf_logger import setup_logger
from src.config.config import JIRA_SERVER, JIRA_TOKEN
from src.core.back.connector import JiraConnector
from src.core.db.connector import SQLiteConnector


def get_jira_connector():
    return JiraConnector(JIRA_SERVER, JIRA_TOKEN)


def main():
    logger = setup_logger(__name__, "snapshooter")
    logger.info("Starting cron job: snapshooter")
    jira = get_jira_connector()


    try:
        snapshot = jira.get_project_open_issues()
        with SQLiteConnector() as db_connector:
            db_connector.clean_db_older_tran_three_days()
            db_connector.snapshot_issues_to_db(snapshot)

    except Exception as e:
        logger.error(f"Błąd podczas przepisywania snapshota: {e}")


if __name__ == '__main__':
    main()
