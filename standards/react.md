# React Rules and Best Practices

## 1. The Rules of Hooks
To use Hooks properly, you must follow these two fundamental rules. React provides an [ESLint plugin](https://npmjs.com) to enforce these automatically.

*   **Only Call Hooks at the Top Level:** Don’t call Hooks inside loops, conditions, or nested functions. Always use Hooks at the top level of your React function, before any early returns. This ensures Hooks are called in the same order each time a component renders.
*   **Only Call Hooks from React Functions:** Don’t call Hooks from regular JavaScript functions. Instead, call them from:
    *   React function components.
    *   Custom Hooks (functions starting with `use`).

## 2. Component Design & Naming
*   **PascalCase Components:** Components must always start with a capital letter (e.g., `UserProfile.js`).
*   **One Component Per File:** For better maintainability, keep one primary component per file.
*   **Functional Components:** Favor functional components with Hooks over older Class components.

## 3. Rendering Rules
*   **Purity:** Keep your components pure. Given the same inputs (props, state, context), a component should always return the same JSX.
*   **Keys in Lists:** Always provide a unique `key` prop when rendering lists of elements to help React identify which items have changed, been added, or removed.
*   **Fragment Shorthand:** Use `<>...</>` instead of unnecessary `<div>` wrappers to keep the DOM clean, unless you need a specific attribute like `key`.

## 4. State Management
*   **Lifting State Up:** If two components need access to the same state, move that state to their closest common ancestor.
*   **State Updates:** Never mutate state directly. Always use the setter function from `useState` or `useReducer`.
*   **Derived State:** Avoid putting data in state if it can be calculated from existing props or state during render.

## 5. Performance & Tooling
*   **Dependency Arrays:** Always include every value used inside an effect (that comes from the component scope) in the `useEffect` dependency array.
*   **Linting:** Use the [Official React ESLint Plugin](https://github.com/jsx-eslint/eslint-plugin-react) to enforce coding standards like prop-sorting and JSX syntax.
*   **Strict Mode:** Always wrap your application in `<React.StrictMode>` during development to find common bugs early.
