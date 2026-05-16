# Clean Code Standards

These rules define the team's clean code guidelines. The code review agent enforces all rules listed here against every staged diff.

---

## 1. Function Length

### Rule 1.1 — 50-Line Function Limit

**Every function must not exceed 50 lines of code.**

- Lines are counted from the `def` (or equivalent) line to the last line of the function body, inclusive.
- Blank lines and comment-only lines inside the function body count toward the limit.
- If a function exceeds 50 lines, it must be decomposed into smaller, single-purpose helper functions.

**Rationale:** Functions longer than 50 lines are difficult to read, test, and reason about. Keeping functions short forces clear separation of concerns.

**Violation example:**
```python
def process_everything(data):
    # ... 60+ lines of mixed logic ...
```

**Compliant example:**
```python
def process_everything(data):
    validated = _validate_input(data)
    transformed = _transform(validated)
    return _persist(transformed)
```

---

## 2. Naming Conventions

### Rule 2.1 — Descriptive Names

Names must clearly communicate intent. Abbreviations and single-letter names (except loop counters `i`, `j`, `k`) are not allowed.

- **Variables/functions:** `snake_case` (Python), `camelCase` (JavaScript/TypeScript)
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private members:** prefix with a single underscore (`_helper`)

**Violation example:**
```python
def fn(d, x):
    tmp = d * x
    return tmp
```

**Compliant example:**
```python
def calculate_total_price(unit_price, quantity):
    total = unit_price * quantity
    return total
```

### Rule 2.2 — Boolean Names Must Be Predicates

Boolean variables and functions that return booleans must start with `is_`, `has_`, `can_`, `should_`, or `was_`.

**Violation example:** `active`, `loaded`, `error`

**Compliant example:** `is_active`, `has_loaded`, `can_submit`

---

## 3. Single Responsibility Principle

### Rule 3.1 — One Responsibility Per Function

Each function must do exactly one thing. If a function's docstring requires the word "and" to describe what it does, it likely violates this rule.

### Rule 3.2 — One Responsibility Per Module/Class

Each module or class must encapsulate a single, well-defined concept. Utility "grab-bag" modules are not permitted.

---

## 4. Comments and Documentation

### Rule 4.1 — No Redundant Comments

Comments must not restate what the code already says clearly.

**Violation example:**
```python
# Increment counter by 1
counter += 1
```

### Rule 4.2 — Explain Why, Not What

Comments should explain non-obvious decisions, trade-offs, or domain context — not describe the mechanics of the code.

**Compliant example:**
```python
# Retry up to 3 times because the upstream API occasionally returns 503
# on the first request due to cold-start latency.
for attempt in range(3):
    ...
```

### Rule 4.3 — All Public Functions Must Have Docstrings

Every public function (not prefixed with `_`) must have a docstring describing its purpose, parameters, and return value.

### Rule 4.4 — Major Code Blocks Must Have Inline Comments

Each logically distinct block within a function (e.g., input validation, data transformation, I/O) must have a brief inline comment identifying its purpose.

---

## 5. Error Handling

### Rule 5.1 — No Bare `except` Clauses

Catching all exceptions silently is forbidden. Always catch a specific exception type.

**Violation example:**
```python
try:
    result = risky_call()
except:
    pass
```

**Compliant example:**
```python
try:
    result = risky_call()
except ValueError as exc:
    logger.warning("Invalid value: %s", exc)
    return default_value
```

### Rule 5.2 — Tools Must Return Error Strings, Not Raise

LangChain tool functions must catch all expected failure modes and return a descriptive error string rather than propagating an exception to the agent.

---

## 6. Code Duplication

### Rule 6.1 — DRY (Don't Repeat Yourself)

Any logic that appears in two or more places must be extracted into a shared function or constant. Copy-pasted code blocks are a violation.

---

## 7. Function Arguments

### Rule 7.1 — Maximum Four Parameters

Functions must not accept more than four positional parameters. If more data is needed, group related parameters into a dataclass or dict.

### Rule 7.2 — No Boolean Flag Arguments

Passing a boolean to switch a function's behaviour is forbidden. Split the function into two clearly named variants instead.

**Violation example:**
```python
def render(component, is_dark_mode=True):
    ...
```

**Compliant example:**
```python
def render_dark(component):
    ...

def render_light(component):
    ...
```

---

## 8. Immutability and Side Effects

### Rule 8.1 — Prefer Pure Functions

Where possible, functions should return new values rather than mutating their inputs. Mutation of function arguments must be documented explicitly in the docstring.

### Rule 8.2 — No Global State Mutation

Functions must not read from or write to module-level mutable state unless the module is explicitly designed as a singleton/registry.
