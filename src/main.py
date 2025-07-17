import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from src.config.config import JIRA_SERVER, JIRA_TOKEN, LIST_OF_AUTHORS
from src.core.back.connector import JiraConnector
from src.core.db.connector import SQLiteConnector

st.set_page_config(layout="wide", page_title='CR')


@st.cache_resource
def get_jira_connector():
    return JiraConnector(JIRA_SERVER, JIRA_TOKEN)

jira = get_jira_connector()


def main() -> None:
    st.title("Stack of cleanups")

    tab1, tab2, tab3  = st.tabs(
        ["Projekt zmiany w issues", "Animator", "Blacklist"]
    )
    with tab1:
        if st.button("Znajdź taski projektu"):
            try:
                issues = jira.get_project_open_issues()
                if not issues:
                    st.info("Brak tasków do cleanupu.")
                else:
                    project_df = pd.DataFrame(issues)
                    print(project_df, flush=True)
                    st.dataframe(project_df,
                                 use_container_width=True,
                                 column_config={"issue_link": st.column_config.LinkColumn(),
                                                "deadline": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:MM"),
                                                "animation_date": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:MM"),  #noqa E501
                                                }
                                 )

            except Exception as e:
                st.error(f"Błąd podczas wyszukiwania: {e}")

    with tab2:
        st.header("Znajdź ID użytkownika JIRA")
        name = st.text_input("Wpisz nazwę użytkownika")

        author_options = [a.strip() for a in LIST_OF_AUTHORS.split("'") if a.strip() and "," not in a]
        selected_author = st.selectbox("Lub wybierz użytkownika z listy:", [""] + author_options)

        if selected_author:
            name = selected_author

        if st.button("Sprawdź ID"):
            if name.strip():
                try:
                    user_name = jira.find_user_id(name)
                    st.success(f"Użytkownik: {user_name} istnieje.")
                except Exception as e:
                    st.error(f"Błąd podczas wyszukiwania: {e}")
            else:
                st.warning("Wprowadź nazwę użytkownika przed kliknięciem przycisku.")

        if st.button("Znajdź taski do cleanupu po użytkowniku"):
            if name.strip():
                try:
                    cleanup_tasks = jira.get_issues_by_artist(name)
                    if not cleanup_tasks:
                        st.info("Brak tasków do cleanupu.")
                    else:
                        df = pd.DataFrame(cleanup_tasks)
                        df = df.sort_values(by=['deadline'], ascending=False)
                        st.dataframe(df,
                                     use_container_width=True,
                                     column_config={"issue_link": st.column_config.LinkColumn(),
                                                    "deadline": st.column_config.DatetimeColumn(
                                                        format="DD/MM/YYYY HH:MM"),
                                                    "animation_date": st.column_config.DatetimeColumn(
                                                        format="DD/MM/YYYY HH:MM"),
                                                    }
                                     )
                except Exception as e:
                    st.error(f"Błąd podczas wyszukiwania: {e}")
            else:
                st.warning("Wprowadź nazwę użytkownika przed kliknięciem przycisku.")

    with tab3:
        st.header("Blacklist – nielistowane taski")

        if "blacklist" not in st.session_state:
            try:
                rows = list()
                with SQLiteConnector() as db_connector:
                    rows = db_connector.fetch_all()
                st.session_state.blacklist = rows
            except Exception as e:
                st.error(f"Błąd podczas pobierania blacklisty: {e}")
                st.session_state.blacklist = []

        blacklist = st.session_state.blacklist

        if not blacklist:
            st.info("Brak zablokowanych tasków.")
        else:
            df_blacklist = pd.DataFrame(blacklist, columns=["ID", "Name"])

            for i in df_blacklist.index:
                id_ = df_blacklist.loc[i, "ID"]
                name = df_blacklist.loc[i, "Name"]
                short_name = name[:5]

                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"- **{name}**")
                with col2:
                    if st.button(f"Usuń filtr na {short_name}", key=f"remove_{id_}"):
                        try:
                            with SQLiteConnector() as db_connector:
                                db_connector.remove_by_id(int(id_))
                                st.success(f"Usunięto z blacklisty: {name}")
                                st.session_state.blacklist = db_connector.fetch_all()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Błąd podczas usuwania z blacklisty: {e}")

if __name__ == '__main__':
    main()
