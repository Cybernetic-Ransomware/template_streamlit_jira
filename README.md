# Event's database handlers for BPOE app
This repository contains a fast prototype app template to perform JQL searches on a Jira Server instance.

## Overview
The purpose of this project is to provide a basic interface for strictly restricted JQL queries over a local network.

## Features
- simple UI with table sorting,
- easy frontend modification using Streamlit components,
- optional deployment with Docker Compose,
- fast setup and access via the local network.

## Requirements
- Python >=3.12.10 with UV package manager
- Docker Desktop / Docker + Compose [optional]

## Getting Started (Windows)
### Deploy
1. Clone the repository:
      ```powershell
      git clone https://github.com/Cybernetic-Ransomware/template_streamlit_jira.git
      ```
2. Set .env file based on the template.
3. Run using Docker:
      ```powershell
      docker compose -f .\docker\docker-compose.yml up --build -d
      ```
### Dev-instance
1. Clone the repository:
      ```powershell
      git clone https://github.com/Cybernetic-Ransomware/template_streamlit_jira.git
      ```
2. Set .env file based on the template.
3. Install UV:
      ```powershell
      pip install uv
      ```
4. Install dependencies:
      ```powershell
      uv sync
      ```
5. Run the application locally:
      ```powershell
      streamlit run .\src\main.py
      ```

## Testing
#### Postman
- Not implemented

#### Pytest
- Not implemented

#### Ruff
```powershell
uv sync --extra dev
uv run ruff check
```
or as a standalone tool:
```powershell
uvx ruff check
```

#### Mypy
```powershell
uv sync --extra dev
uv run mypy .\src\
```
or as a standalone tool:
```powershell
uvx mypy .\src\
```

## Useful links and documentation
- Jira Atlassian Python API: [Atlassian](https://atlassian-python-api.readthedocs.io/jira.html)
- Deploy Streamlit using Docker: [TimescaleDB](https://docs.streamlit.io/deploy/tutorials/docker)
- Advanced JQL searching: [Atlassian](https://confluence.atlassian.com/jirasoftwareserver0822/advanced-searching-1142432445.html)
