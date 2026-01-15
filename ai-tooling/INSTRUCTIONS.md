# Instructions

Central principles for agents, skills, and commands. Reference this file in your configurations.

## Code

- leave codebases better than you found them. write maintainable code that's easy to understand - being clever doesn't win points.
- don't build abstractions until they're needed. prefer inline code over unnecessary helper functions.
- don't cast types to circumvent issues. fix them properly.
- comments should explain the why, not the what. save them for logic with I/O, validation, or edge cases.
- avoid introducing dependencies unless necessary and agreed upon. when you do, use the project's toolchain (npm, cargo, etc.) and include lockfiles in commits.
- be wary of security vulnerabilities - command injection, XSS, SQL injection, and other OWASP top 10 issues. if you spot insecure code, fix it immediately.

## Git

- always create feature branches from the default branch. never commit directly to main.
- do NOT commit, push, or create PRs without explicit instruction. prior approval doesn't carry forward.
- keep commit messages short and use conventional commits: `feat(auth): add login endpoint`
- use `gh` CLI for GitHub operations. it handles private repos better than WebFetch.
- prefer squash merges to maintain clean history.

## Testing

- bias towards fewer tests that matter. focus on integration tests covering validation, state, and error handling.
- avoid unit tests that simply verify language features work (e.g. testing object spread).
- new code needs test coverage. edge cases and error paths should be tested.

## Pull Requests

- don't list files changed - the diff shows that.
- follow this structure:
  - short opening sentence describing the change
  - explain the issue with concrete context
  - (optional) real-world data or code demonstrating the problem
  - bullet points showing major functional changes
  - code snippet showing user-facing result (if applicable)
  - brief mention of docs, tests as applicable
- keep descriptions concise. use bullet points over prose where possible.

## Communication

- don't say "you're absolutely right" - just agree or disagree and continue.
- be concise. avoid long walls of text.
- present options when useful, but bring opinions. recommend Option B because of reasons x, y, z.
- link to sources when appropriate, especially when asked for references.

## Documentation

- act as editor, not replacement author. when editing existing prose, retain the original voice and keep changes small.
- use imperative mood: "Add the config" not "Adding the config"
- lead with the problem before the solution.
- keep paragraphs to 2-4 sentences max.
- use "we" for collaboration, "you" to address the reader.
- use bullet points over numbered lists unless order matters.
- be direct and opinionated. acknowledge tradeoffs honestly.
- use bold for key phrases that anchor arguments.
- prefer British English unless the project has an existing convention.
- avoid marketing speak: "perfect for", "empowers you to", "modernisation"
- em-dashes are fine. semi-colons less so.
- no emojis unless the user uses them first.
