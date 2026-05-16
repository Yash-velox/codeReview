# Requirements Document

## Introduction

A Python-based Code Review Agent that uses Grok (via xAI API) as its reasoning engine. The agent follows a structured multi-tool reasoning path to review staged code changes against Jira ticket requirements and team-specific coding standards defined in local Markdown files. It produces a structured Markdown report identifying missing requirements, code quality violations, and suggested fixes.

## Glossary

- **Agent**: The LangChain-powered orchestrator that coordinates tool calls and produces the final review report.
- **Grok_LLM**: The Grok-1 model accessed via the xAI API using an OpenAI-compatible client.
- **JiraContextRetriever**: A LangChain Tool that fetches ticket metadata (title, description, acceptance criteria) from a Jira instance.
- **GitDiffCollector**: A LangChain Tool that captures staged code changes via `git diff --staged`.
- **RulesEngineReader**: A LangChain Tool that reads all `.md` files from the local `/standards` directory and returns a consolidated rules string.
- **Standards_Directory**: A local directory named `/standards` containing Markdown files that define team coding rules (e.g., `tailwind_rules.md`, `clean_code.md`).
- **Review_Report**: The final Markdown-formatted output produced by the Agent containing missing requirements, code quality violations, and suggested fixes.
- **Ticket_ID**: A string identifier for a Jira issue (e.g., `PROJ-123`).

---

## Requirements

### Requirement 1: Environment Configuration

**User Story:** As a developer, I want the agent to load credentials and URLs from environment variables, so that secrets are never hardcoded in source files.

#### Acceptance Criteria

1. THE Agent SHALL load `XAI_API_KEY`, `JIRA_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` from a `.env` file using `python-dotenv`.
2. IF any required environment variable is missing at startup, THEN THE Agent SHALL raise a descriptive `EnvironmentError` identifying the missing variable by name.
3. THE Agent SHALL never expose environment variable values in logs or console output.

---

### Requirement 2: Jira Context Retrieval

**User Story:** As a code reviewer, I want the agent to fetch Jira ticket details, so that it can verify the code satisfies the stated requirements.

#### Acceptance Criteria

1. WHEN a `ticket_id` string is provided, THE JiraContextRetriever SHALL connect to the Jira instance using `atlassian-python-api` and retrieve the ticket's title, description, and acceptance criteria fields.
2. WHEN the Jira ticket is successfully retrieved, THE JiraContextRetriever SHALL return a structured string containing the title, description, and acceptance criteria.
3. IF the `ticket_id` does not correspond to an existing Jira ticket, THEN THE JiraContextRetriever SHALL return an error string describing the failure without raising an unhandled exception.
4. IF the Jira API is unreachable, THEN THE JiraContextRetriever SHALL return an error string describing the connectivity failure without raising an unhandled exception.

---

### Requirement 3: Git Diff Collection

**User Story:** As a code reviewer, I want the agent to capture staged code changes automatically, so that the review is always based on the exact diff about to be committed.

#### Acceptance Criteria

1. WHEN invoked, THE GitDiffCollector SHALL execute `git diff --staged` via the `subprocess` module and return the full output as a string.
2. IF no files are staged, THEN THE GitDiffCollector SHALL return a string indicating that no staged changes were found.
3. IF the `git` command is not available or the working directory is not a git repository, THEN THE GitDiffCollector SHALL return a descriptive error string without raising an unhandled exception.

---

### Requirement 4: Coding Standards Ingestion

**User Story:** As a team lead, I want the agent to read all Markdown rule files from the standards directory, so that reviews are always consistent with the latest team guidelines.

#### Acceptance Criteria

1. WHEN invoked, THE RulesEngineReader SHALL scan the `/standards` directory and read all files with a `.md` extension.
2. THE RulesEngineReader SHALL concatenate the contents of all discovered `.md` files into a single consolidated context string, preserving each file's content under a labelled section header derived from the filename.
3. IF the `/standards` directory does not exist or contains no `.md` files, THEN THE RulesEngineReader SHALL return a descriptive error string without raising an unhandled exception.
4. THE RulesEngineReader SHALL strictly enforce the rule that no function in reviewed code exceeds 50 lines, as defined in the standards files.

---

### Requirement 5: Agent Initialization and LLM Configuration

**User Story:** As a developer, I want the agent to use Grok-1 via the xAI API, so that the review leverages a capable LLM through a standard interface.

#### Acceptance Criteria

1. THE Agent SHALL initialize the Grok_LLM using `langchain-openai`'s `ChatOpenAI` class with `base_url="https://api.x.ai/v1"` and the `XAI_API_KEY` loaded from the environment.
2. THE Agent SHALL be constructed using the LangChain `create_react_agent` or OpenAI Functions Agent pattern, binding all three tools: JiraContextRetriever, GitDiffCollector, and RulesEngineReader.
3. THE Agent SHALL be configured with a system prompt that defines its persona as a "Pedantic Senior Code Reviewer".

---

### Requirement 6: Agent Reasoning Sequence

**User Story:** As a code reviewer, I want the agent to follow a defined reasoning order, so that the review is thorough and reproducible.

#### Acceptance Criteria

1. WHEN a review is initiated with a `ticket_id`, THE Agent SHALL first invoke JiraContextRetriever to obtain the Jira context.
2. WHEN Jira context has been obtained, THE Agent SHALL invoke GitDiffCollector to obtain the staged diff.
3. WHEN the staged diff has been obtained, THE Agent SHALL invoke RulesEngineReader to obtain the consolidated coding standards.
4. WHEN all three context sources have been gathered, THE Agent SHALL apply the coding standards to the diff and compare the diff against the Jira acceptance criteria.

---

### Requirement 7: Review Report Generation

**User Story:** As a developer, I want to receive a structured Markdown report after each review, so that I can quickly understand what needs to be fixed before committing.

#### Acceptance Criteria

1. WHEN the analysis is complete, THE Agent SHALL produce a Review_Report in Markdown format.
2. THE Review_Report SHALL contain a "Missing Requirements" section listing any Jira acceptance criteria not addressed by the diff.
3. THE Review_Report SHALL contain a "Code Quality Violations" section listing violations of the standards rules, including Tailwind CSS usage issues and any function exceeding 50 lines.
4. THE Review_Report SHALL contain a "Suggested Fixes" section providing concrete, actionable recommendations for each identified issue.
5. IF no issues are found, THEN THE Agent SHALL produce a Review_Report stating that the code satisfies all requirements and standards.

---

### Requirement 8: Modularity and Code Style

**User Story:** As a maintainer, I want the codebase to be modular and well-commented, so that individual tools can be extended or replaced independently.

#### Acceptance Criteria

1. THE Agent's codebase SHALL be organized so that each tool (JiraContextRetriever, GitDiffCollector, RulesEngineReader) is defined in its own module or clearly separated function.
2. THE Agent's codebase SHALL ensure no single function exceeds 50 lines of code.
3. THE Agent's codebase SHALL include inline comments explaining the purpose of each major code block.
4. WHERE a new tool is added, THE Agent SHALL allow it to be registered without modifying existing tool implementations.
