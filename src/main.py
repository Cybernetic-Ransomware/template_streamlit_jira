import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from src.config.config import JIRA_SERVER, JIRA_TOKEN, PROJECT_NAME
from src.core.back.connector import JiraConnector
from src.core.db.connector import SQLiteConnector

st.set_page_config(layout="wide", page_title='CR')


@st.cache_resource
def get_jira_connector():
    return JiraConnector(JIRA_SERVER, JIRA_TOKEN)

jira = get_jira_connector()

def get_project_open_issues_df() -> pd.DataFrame:
    issues = jira.get_project_open_issues_filtered()
    project_df = pd.DataFrame(issues)

    project_df['count_attachments'] = project_df['attachments'].apply(lambda x: len(x))
    project_df['count_comments'] = project_df['comments'].apply(lambda x: len(x))

    cols = project_df.columns.tolist()

    if "attachments" in cols and "count_attachments" in cols:
        attachments_index = cols.index("attachments")
        cols.remove("count_attachments")
        cols.insert(attachments_index + 1, "count_attachments")

    if "comments" in cols and "count_comments" in cols:
        comments_index = cols.index("comments")
        cols.remove("count_comments")
        cols.insert(comments_index + 1, "count_comments")

    return project_df[cols]


def main() -> None:
    st.title(f"Comparisons project: {PROJECT_NAME.capitalize()}")

    tab1, tab2, tab3  = st.tabs(
        ["Otwarte Issues", "Zmiany w Issues", "Manual_snapshot"]
    )
    with tab1:
        if st.button("Znajdź taski projektu"):
            try:
                project_df = get_project_open_issues_df()
                if project_df.empty:
                    st.info("Brak tasków.")
                else:
                    # ruff: noqa: E501
                    st.dataframe(project_df,
                                 use_container_width=True,
                                 column_config={"name": st.column_config.TextColumn(label="Issue"),
                                                "issue_link": st.column_config.LinkColumn(label="Link", width="small",
                                                                                          max_chars=12, display_text=r"https://jira\.gpd\.com\.pl/browse/([^/]+)"),
                                                "description": st.column_config.TextColumn(label="Description", width="large", max_chars=120, help="Kliknij, aby rozwinąć"),
                                                "deadline": st.column_config.DatetimeColumn(label="Deadline", format="DD/MM/YYYY HH:MM"),
                                                "attachments": st.column_config.ListColumn(label="Załączniki z ostatnich 3 dni", help="Kliknij, aby rozwinąć"),
                                                "count_attachments": st.column_config.NumberColumn(label="SUM"),
                                                "comments": st.column_config.ListColumn(label="Komentarze z ostatnich 3 dni", help="Kliknij, aby rozwinąć"),
                                                "count_comments": st.column_config.NumberColumn(label="SUM"),
                                                },
                                 hide_index=True
                                 )
                    # ruff: enable=E501

            except Exception as e:
                st.error(f"Błąd podczas wyszukiwania: {e}")

    with tab2:
        if st.button("Znajdź zmiany w taskach"):
            try:
                issues = None
                if not issues:
                    st.info("Brak tasków")
                else:
                    project_df = pd.DataFrame(issues)
                    project_df.drop(columns=["current_timestamp"], axis=1, inplace=True)
                    project_df['count_attachments'] = project_df['attachments'].apply(lambda x: len(x))
                    project_df['count_comments'] = project_df['comments'].apply(lambda x: len(x))

                    # changing sum columns order
                    cols = project_df.columns.tolist()

                    attachments_index = cols.index("attachments")
                    cols.remove("count_attachments")
                    cols.insert(attachments_index + 1, "count_attachments")

                    comments_index = cols.index("comments")
                    cols.remove("count_comments")
                    cols.insert(comments_index + 1, "count_comments")

                    project_df = project_df[cols]

                    # ruff: noqa: E501
                    st.dataframe(project_df,
                                 use_container_width=True,
                                 column_config={"name": st.column_config.TextColumn(label="Issue"),
                                                "issue_link": st.column_config.LinkColumn(label="Link", width="small",
                                                                                          max_chars=12,
                                                                                          display_text=r"https://jira\.gpd\.com\.pl/browse/([^/]+)"),
                                                "description": st.column_config.TextColumn(label="Description",
                                                                                           width="large", max_chars=120,
                                                                                           help="Kliknij, aby rozwinąć"),
                                                "deadline": st.column_config.DatetimeColumn(label="Deadline",
                                                                                            format="DD/MM/YYYY HH:MM"),
                                                "attachments": st.column_config.ListColumn(
                                                    label="Załączniki z ostatnich 3 dni", help="Kliknij, aby rozwinąć"),
                                                "count_attachments": st.column_config.NumberColumn(label="SUM"),
                                                "comments": st.column_config.ListColumn(
                                                    label="Komentarze z ostatnich 3 dni", help="Kliknij, aby rozwinąć"),
                                                "count_comments": st.column_config.NumberColumn(label="SUM"),
                                                },
                                 hide_index=True
                                 )
                    # ruff: enable=E501

            except Exception as e:
                st.error(f"Błąd podczas wyszukiwania: {e}")

    with tab3:
        st.header("Snapshot")

        if st.button("Manual snapshot"):
            try:
                snapshot = jira.get_project_open_issues()
                with SQLiteConnector() as db_connector:
                    db_connector.snapshot_issues_to_db(snapshot)

            except Exception as e:
                st.error(f"Błąd podczas przepisywania snapshota: {e}")


        if "blacklist" not in st.session_state:
            try:
                rows = list()
                with SQLiteConnector() as db_connector:
                    rows = db_connector.fetch_all()
                st.session_state.blacklist = rows
            except Exception as e:
                st.error(f"Błąd podczas pobierania blacklisty: {e}")
                st.session_state.blacklist = []

if __name__ == '__main__':
    main()
