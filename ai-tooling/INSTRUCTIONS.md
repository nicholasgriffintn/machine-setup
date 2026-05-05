# Instructions

Central principles for agents, skills, and commands. Reference this file in your configurations.

## Code

- Leave codebases better than you found them.
- Write maintainable code that is easy to understand.
- Avoid speculative abstractions.
- Do not grow route/page files with feature internals.
- Route files should orchestrate data loading and composition.
- If logic is non-trivial (state machine, parsing, measurement, timers, or >25–40 lines), extract it to a component/hook/lib module immediately.
- Do not cast types to circumvent issues. Fix them properly.
- Comments should explain why, not what.
- Use comments sparingly for I/O, validation, and edge cases.
- Avoid introducing dependencies unless necessary and agreed upon.
- When adding dependencies, use the project toolchain and include lockfiles in commits.

## Shared Utilities

- Treat reusable helper logic as shared by default, not inline.
- Before writing any helper, search the repo for an existing utility and reuse it when possible.
- Do not define generic utilities inside feature files, route files, or service files.
- Generic helpers include serialisation, parsing, string/date/number helpers, type guards, validators, formatters, mappers, and error helpers.
- Generic helpers must live in shared utility modules.
- If an inline utility is introduced during a task, move it to a shared utility module in the same patch.
- Treat violations of these rules as defects and fix them immediately.
- If unsure whether logic is generic, treat it as generic and put it in shared utilities.

## Security

- Be wary of OWASP Top 10 issues.
- If you spot insecure code, fix it immediately.
- Pay particular attention to command injection, XSS, SQL injection, auth bypass, and insecure defaults.

## Testing

- Bias toward fewer tests that matter.
- Prefer integration tests that cover validation, state transitions, and error handling.
- Avoid unit tests that only verify language features.
- New code needs coverage.
- Test edge cases and error paths.

## Communication

- Be concise.
- Avoid long walls of text.
- Present options when useful, but bring opinions.
- Recommend a preferred option with reasons.
- Link to sources when appropriate, especially when asked for references.
- Do not use the phrase “you’re absolutely right”.

## Documentation

- Act as editor, not replacement author.
- When editing prose, retain original voice and keep changes small.
- Use imperative mood.
- Lead with the problem before the solution.
- Keep paragraphs to 2–4 sentences.
- Use “we” for collaboration and “you” for the reader.
- Prefer bullet points over numbered lists unless order matters.
- Be direct and opinionated.
- Acknowledge trade-offs honestly.
- Use bold for key anchor phrases.
- Prefer British English unless the project has an existing convention.
- Avoid marketing language.
- Em-dashes are fine. Semicolons less so.
- No emojis unless the user uses them first.

## Git

- Always create feature branches from the default branch.
- Never commit directly to `main`.
- Do not commit, push, or create PRs without explicit instruction.
- Prior approval does not carry forward.
- Keep commit messages short and use conventional commits.
- Use `gh` CLI for GitHub operations.
- Prefer squash merges to keep history clean.

## Pull Requests

- Do not list files changed.
- Use this structure:
- Short opening sentence describing the change.
- Explain the issue with concrete context.
- Optional real-world data or code demonstrating the problem.
- Bullet points of major functional changes.
- User-facing code snippet when applicable.
- Brief mention of docs and tests when applicable.
- Keep descriptions concise.

## Scope and Priority

- These rules apply to every task in every repository.
- Treat this file as a strict contract, not guidance.
- When rules conflict, follow the stricter rule.
- If a rule is ambiguous, choose the safest, most maintainable, least invasive interpretation.
- Do not trade instruction compliance for speed.

## Definition of Done (Hard Gate)

A task is not complete unless all are true:

- Code follows this contract and repo conventions.
- No structural violations remain in changed files.
- Relevant validation has run, or a blocker is stated explicitly.
- Risks, assumptions, and follow-ups are stated briefly.

## Required Final Response Format

Every final response must include:

- `Compliance:` pass/fail against this contract.
- `Validation:` commands run and result.
- `Residual risks:` none or short list.

Keep the output concise and focused on these points. Do not include extraneous information.
