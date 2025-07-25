import json
import re
from typing import Any

import pendulum
import urllib3
from atlassian import Jira

from src.config.conf_logger import setup_logger
from src.config.config import JIRA_SERVER, PROJECT_NAME

logger = setup_logger(__name__, "jira")


class JiraConnector:
    connector: Jira

    def __init__(self, server: str, token: str):
        self.connector = Jira(server, token=token, verify_ssl=False)
        self.jira_warnings = urllib3.disable_warnings  # warnings from verify_ssl=False
        self.jira_warnings()

    def _find_user_id(self, name: str) -> dict:
        raw_response = self.connector.user_find_by_user_string(username=name, start=0, limit=50,
                                                               include_inactive_users=False)

        response = dict()
        response["key"] = raw_response[0].get("key") if isinstance(raw_response, list) and raw_response else raw_response
        response["name"] = raw_response[0].get("name") if isinstance(raw_response, list) and raw_response else raw_response

        return response

    def find_user_id(self, name: str) -> str:
        return self._find_user_id(name).get('name', 'No name found')

    def get_issues_by_artist(self, artist: str) -> list:
        artist_id = self._find_user_id(artist).get('name')
        logger.info(f"Requested an artist by the phase: {artist} - found: {artist_id}")
        if artist_id is None:
            return ['No artist found']
        jql_request = f'status!=Closed  AND Description ~ "clean" AND Animator in ({json.dumps(artist_id)})'
        issues = self.connector.jql(jql_request).get("issues", {})  # type: ignore[union-attr]

        list_of_responses = list()
        response = dict()
        for issue in issues:
            issue_name = issue.get('fields').get('summary')
            response['name'] = issue_name

            deadline = issue.get('fields').get('customfield_11200')
            deadline_ts = pendulum.from_format(deadline, 'YYYY-MM-DDTHH:mm:ss.SSSZ', tz='Europe/Warsaw', locale='pl')
            response['deadline'] = deadline_ts.strftime("%d/%m/%Y %H:%M")

            animation_date = issue.get('fields').get('customfield_18802')
            animation_date_ts = pendulum.from_format(animation_date, 'YYYY-MM-DDTHH:mm:ss.SSSZ', tz='Europe/Warsaw',
                                                     locale='pl')
            response['animation_date'] = animation_date_ts.strftime("%d/%m/%Y %H:%M")

            animators = [animator.get('name') for animator in issue.get('fields').get('customfield_11913')]
            response["signed_animators"] = animators

            issue_link = JIRA_SERVER + r'browse/' + str(issue.get('key'))
            response['issue_link'] = issue_link

            list_of_responses.append(response)
            response = dict()

        return list_of_responses

    def get_project_open_issues(self) -> list[dict[str, Any]]:
        jql_request = f'project = {PROJECT_NAME} AND status != Closed'
        issues = self.connector.jql(jql_request).get("issues", {})  # type: ignore[union-attr]

        response: dict[str, Any] = {}  #mupy calmer
        list_of_responses = list()
        for issue in issues:
            response = dict()
            current_timestamp = pendulum.now(tz='Europe/Warsaw')
            response['current_timestamp'] = current_timestamp

            issue_name = issue.get('fields').get('summary')
            response['name'] = issue_name

            issue_link = JIRA_SERVER + r'browse/' + str(issue.get('key'))
            response['issue_link'] = issue_link

            description = issue.get('fields').get('description')
            response['description'] = description

            deadline = issue.get('fields').get('customfield_11200', None)
            if deadline:
                deadline_ts = pendulum.from_format(deadline, 'YYYY-MM-DDTHH:mm:ss.SSSZ', tz='Europe/Warsaw', locale='pl')
                # response['deadline'] = deadline_ts.strftime("%d/%m/%Y %H:%M")
                response['deadline'] = deadline_ts
            else:
                response['deadline'] = None

            response['attachments'] = list()
            response['comments'] = list()

            comments_raw = issue.get('fields', {}).get('comment', {}).get('comments', [])
            comments = [
                {
                    "id": comment.get("id"),
                    "author": comment.get("author", {}).get("name", ""),
                    "url": comment.get("self", ""),
                    "body": re.sub(r'\[~.*?\]', '', comment.get("body"))[:24],
                    "created":  pendulum.parse(comment.get("created")).in_timezone("Europe/Warsaw"),  # type: ignore[union-attr]
                    "updated":  pendulum.parse(comment.get("updated")).in_timezone("Europe/Warsaw")  # type: ignore[union-attr]
                }
                for comment in comments_raw
            ]
            filter_date = pendulum.now(tz='Europe/Warsaw').add(days=-3)
            filtered_sorted = sorted(
                (c for c in comments if c["created"] > filter_date or c["updated"] > filter_date),
                key=lambda x: x["updated"],
                reverse=True
            )

            response['comments'] = [
                f"{c['author']} | {c['body']} | {c['url']}" for c in filtered_sorted
            ]
            # response['comments'] = comments

            attachments_raw = issue.get('fields', {}).get('attachment', [])
            attachments = [
                {
                    "id": attachment.get("id"),
                    "name": attachment.get("filename"),
                    "url": attachment.get("self")
                }
                for attachment in attachments_raw
            ]
            response['attachments'] = [f"[{att['name']}]({att['url']})" for att in attachments]
            # response['attachments'] = "\n".join(f"[{att['name']}]({att['url']})" for att in attachments)

            list_of_responses.append(response)

        # print(list_of_responses, flush=True)
        return list_of_responses
