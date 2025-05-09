import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from src.config.config import JIRA_SERVER, JIRA_TOKEN, LIST_OF_AUTHORS
from src.core.back.connector import JiraConnector

jira = JiraConnector(JIRA_SERVER, JIRA_TOKEN)

def main() -> None:
    st.set_page_config(layout="wide", page_title='CR')
    st.title("Stack of cleanups")

    tab1, tab2  = st.tabs(
        ["Wszystkie cleanupy", "Animator",]
    )

    with tab1:
        if st.button("Znajdź taski do cleanupu"):
            try:
                cleanup_tasks = jira.get_cleanup_issues()
                if not cleanup_tasks:
                    st.info("Brak tasków do cleanupu.")
                else:
                    df = pd.DataFrame(cleanup_tasks)
                    df = df.sort_values(by=['deadline'], ascending=False)

                    st.dataframe(df,
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

if __name__ == '__main__':
    main()
