import difflib
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import pendulum
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
                                                "description": st.column_config.TextColumn(label="Description", width="large",
                                                                                           max_chars=120, help="Kliknij, aby rozwinąć"),
                                                "deadline": st.column_config.DatetimeColumn(label="Deadline",
                                                                                            format="DD/MM/YYYY HH:mm"),
                                                "attachments": st.column_config.ListColumn(label="Załączniki z ostatnich 3 dni",
                                                                                           help="Kliknij, aby rozwinąć"),
                                                "count_attachments": st.column_config.NumberColumn(label="SUM"),
                                                "comments": st.column_config.ListColumn(label="Komentarze z ostatnich 3 dni",
                                                                                        help="Kliknij, aby rozwinąć"),
                                                "count_comments": st.column_config.NumberColumn(label="SUM"),
                                                },
                                 hide_index=True
                                 )
                    # ruff: enable=E501

            except Exception as e:
                st.error(f"Błąd podczas wyszukiwania: {e}")

    with tab2:
        if "project_df" not in st.session_state:
            st.session_state.project_df = pd.DataFrame()

        if "selected_key" not in st.session_state:
            st.session_state.selected_key = None

        if "diff_list" not in st.session_state:
            st.session_state.diff_list = []

        snapshot_mapping = {
            "last_one": lambda: pendulum.now().to_iso8601_string(),
            "first_yesterday": lambda: pendulum.yesterday().to_iso8601_string(),
            "first_three_days_ago": lambda: pendulum.today().subtract(days=3).to_iso8601_string(),
        }

        tab2_col1, tab2_col2, tab2_col3 = st.columns(3)

        with tab2_col1:
            if st.button("Znajdź zmiany względem ostatniego snapshotu"):
                st.session_state.selected_key = "last_one"
        with tab2_col2:
            if st.button("Znajdź zmiany względem pierwszego wczoraj"):
                st.session_state.selected_key = "first_yesterday"
        with tab2_col3:
            if st.button("Znajdź zmiany względem pierwszego sprzed trzech dni"):
                st.session_state.selected_key = "first_three_days_ago"

        if st.session_state.selected_key:
            try:
                project_dict = jira.get_project_open_issues()
                st.session_state.project_df = pd.DataFrame(project_dict)

                if st.session_state.project_df.empty:
                    st.info("Brak tasków.")
                    st.session_state.diff_list = []
                else:
                    diff_list = []
                    with SQLiteConnector() as db_connector:
                        date_to_compare = snapshot_mapping[st.session_state.selected_key]()

                        for _, row in st.session_state.project_df.iterrows():
                            issue_key = row['issue_link'].split("/")[-1]
                            snap_dict = db_connector.get_closest_past_snapshot(issue_key, date_to_compare)

                            if not snap_dict:
                                continue

                            current = row.to_dict()
                            diff = {
                                "name": current.get("name"),
                                "issue_link": row['issue_link'],
                                "snap_time": snap_dict.get("current_timestamp", None)
                            }
                            template_diff_count = len(diff)

                            if str(current.get("deadline")) != str(snap_dict.get("deadline")):
                                snap_date = pendulum.parse(snap_dict.get('deadline')).format('YY/MM/DD HH:mm')  # type: ignore[union-attr]
                                current_date = current.get('deadline').format('YY/MM/DD HH:mm')  # type: ignore[union-attr]
                                diff["deadline"] = f"{snap_date} → {current_date}"

                            old_desc = str(snap_dict.get("description")).splitlines()
                            new_desc = str(current.get("description")).splitlines()
                            if old_desc != new_desc:
                                diff_lines = list(difflib.unified_diff(
                                    old_desc,
                                    new_desc,
                                    fromfile='poprzedni snap',
                                    tofile='obecnie jira',
                                    lineterm=''
                                ))
                                diff["description"] = "\n".join(diff_lines)

                            if len(snap_dict.get("comments", [])) != len(current.get("comments", [])):
                                diff[
                                    "comments_count"] = f"{len(snap_dict.get('comments', []))} → {len(current.get('comments', []))}"

                            if len(snap_dict.get("attachments", [])) != len(current.get("attachments", [])):
                                diff[
                                    "attachments_count"] = f"{len(snap_dict.get('attachments', []))} → {len(current.get('attachments', []))}"

                            if len(diff) > template_diff_count:
                                diff_list.append(diff)

                    st.session_state.diff_list = diff_list

            except Exception as e:
                st.error(f"Błąd podczas wyszukiwania: {e}")

        if not st.session_state.project_df.empty:
            if not st.session_state.diff_list:
                st.success("Brak zmian względem wybranego snapshotu.")
            else:
                # ruff: noqa: E501
                st.dataframe(pd.DataFrame(st.session_state.diff_list),
                             use_container_width=True,
                             column_config={"name": st.column_config.TextColumn(label="Issue"),
                                            "issue_link": st.column_config.LinkColumn(label="Link", width="small",
                                                                                      max_chars=12, display_text=r"https://jira\.gpd\.com\.pl/browse/([^/]+)"),
                                            "snap_time": st.column_config.DatetimeColumn(label="Czas zapisanego snapa",
                                                                                        format="DD/MM/YYYY HH:mm"),
                                            "deadline": st.column_config.TextColumn(label="Deadline",
                                                                                    width="small", max_chars=35),
                                            "comments_count": st.column_config.TextColumn(label="Ilość komentarzy",
                                                                                          width="small", max_chars=14),
                                            "attachments_count": st.column_config.TextColumn(label="Ilość załączników",
                                                                                             width="small", max_chars=12),
                                            "description": st.column_config.TextColumn(label="Description", width="large",
                                                                                       max_chars=120, help="Kliknij, aby rozwinąć"),
                                            },
                             hide_index=True
                             )
                # ruff: enable=E501

    with tab3:
        st.header("Snapshot")

        if st.button("Manual snapshot"):
            try:
                snapshot = jira.get_project_open_issues()
                with SQLiteConnector() as db_connector:
                    db_connector.clean_db_older_tran_three_days()
                    db_connector.snapshot_issues_to_db(snapshot)

            except Exception as e:
                st.error(f"Błąd podczas przepisywania snapshota: {e}")

if __name__ == '__main__':
    main()
