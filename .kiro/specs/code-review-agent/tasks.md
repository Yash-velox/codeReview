# Tasks

## Task List

- [x] 1. Project scaffold and environment setup
  - [x] 1.1 Create project directory structure (`tools/`, `standards/`, `tests/`)
  - [x] 1.2 Create `requirements.txt` with pinned dependencies: `langchain`, `langchain-openai`, `atlassian-python-api`, `python-dotenv`, `hypothesis`
  - [x] 1.3 Create `.env.example` listing all four required variables with placeholder values

- [x] 2. Environment configuration module (`config.py`)
  - [x] 2.1 Implement `load_config()` that reads `.env` via `python-dotenv` and returns an `AppConfig` dataclass
  - [x] 2.2 Raise `EnvironmentError` naming any missing variable
  - [x] 2.3 Ensure no secret values are passed to the logging layer
  - [x] 2.4 Write property tests for Properties 1–3 (`tests/test_config.py`)

- [x] 3. JiraContextRetriever tool (`tools/jira_tool.py`)
  - [x] 3.1 Implement `fetch_jira_context(ticket_id)` using `atlassian-python-api`
  - [x] 3.2 Return structured string with title, description, acceptance criteria on success
  - [x] 3.3 Return descriptive error string (no exception) for missing ticket and connectivity failure
  - [x] 3.4 Register as a LangChain `Tool` with name and description
  - [x] 3.5 Write property tests for Properties 4–5 (`tests/test_jira_tool.py`)

- [x] 4. GitDiffCollector tool (`tools/git_tool.py`)
  - [x] 4.1 Implement `collect_git_diff()` using `subprocess` to run `git diff --staged`
  - [x] 4.2 Return diff string on success; return descriptive string for no staged files or non-git-repo
  - [x] 4.3 Register as a LangChain `Tool`
  - [x] 4.4 Write property tests for Property 6 (`tests/test_git_tool.py`)

- [x] 5. RulesEngineReader tool (`tools/rules_tool.py`)
  - [x] 5.1 Implement `read_coding_standards()` to scan `/standards/*.md`
  - [x] 5.2 Concatenate file contents under labelled section headers derived from filenames
  - [x] 5.3 Return descriptive error string (no exception) when directory is missing or empty
  - [x] 5.4 Register as a LangChain `Tool`
  - [x] 5.5 Write property tests for Properties 7–8 (`tests/test_rules_tool.py`)

- [x] 6. Agent initialization (`agent.py`)
  - [x] 6.1 Implement `build_agent(config)` initialising `ChatOpenAI` with `base_url="https://api.x.ai/v1"` and `XAI_API_KEY`
  - [x] 6.2 Bind all three tools to the agent via `create_react_agent`
  - [x] 6.3 Set system prompt defining the "Pedantic Senior Code Reviewer" persona
  - [x] 6.4 Write unit tests verifying `base_url`, `api_key`, and system prompt content (`tests/test_agent.py`)

- [x] 7. Agent reasoning sequence and report generation
  - [x] 7.1 Configure agent/system prompt to enforce Jira → Git diff → Rules invocation order
  - [x] 7.2 Ensure the final output is a Markdown report with "Missing Requirements", "Code Quality Violations", and "Suggested Fixes" sections
  - [x] 7.3 Handle the no-issues case with a clean-pass message
  - [x] 7.4 Write property tests for Properties 9–10 (`tests/test_agent.py`)

- [x] 8. CLI entry point (`main.py`)
  - [x] 8.1 Parse `ticket_id` from CLI arguments
  - [x] 8.2 Call `load_config()`, `build_agent()`, run the agent, and print the report
  - [x] 8.3 Exit with a non-zero code and human-readable message on `EnvironmentError` or `RuntimeError`

- [x] 9. Sample standards files
  - [x] 9.1 Create `standards/clean_code.md` with at least the 50-line function rule
  - [x] 9.2 Create `standards/tailwind_rules.md` with sample Tailwind CSS usage rules

- [ ] 10. Final validation
  - [ ] 10.1 Verify all functions in the codebase are ≤ 50 lines
  - [~] 10.2 Verify each module has inline comments on major code blocks
  - [~] 10.3 Run full test suite (`pytest tests/`) and confirm all tests pass
