---
name: review-pr
description: Review a PR on runner-manager (Python FastAPI service managing GitHub Actions self-hosted runners on cloud VMs)
argument-hint: <pr-number-or-url>
disable-model-invocation: true
allowed-tools: Read, Bash(gh repo view *), Bash(gh pr view *), Bash(gh pr diff *), Bash(gh pr comment *), Bash(gh api *), Bash(git diff *), Bash(git log *), Bash(git show *)
---

# Review GitHub PR

You are an expert code reviewer. Review this PR: $ARGUMENTS

## Determine PR target

Parse `$ARGUMENTS` to extract the repo and PR number:

- If arguments contain `REPO:` and `PR_NUMBER:` (CI mode), use those values directly.
- If the argument is a GitHub URL (starts with `https://github.com/`), extract `owner/repo` and the PR number from it.
- If the argument is just a number, use the current repo from `gh repo view --json nameWithOwner -q .nameWithOwner`.

## Output mode

- **CI mode** (arguments contain `REPO:` and `PR_NUMBER:`): post inline comments and summary to GitHub.
- **Local mode** (all other cases): output the review as text directly. Do NOT post anything to GitHub.

## Steps

1. **Fetch PR details:**

```bash
gh pr view <number> --repo <owner/repo> --json title,body,headRefOid,author,files
gh pr diff <number> --repo <owner/repo>
```

1. **Read changed files** to understand the full context around each change (not just the diff hunks).

1. **Analyze the changes** against these criteria:

| Area                              | What to check                                                                                                                                                                                 |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Async error handling              | Uncaught exceptions in async FastAPI endpoints; background RQ jobs that swallow errors silently; missing `try/except` around cloud provider API calls that can fail transiently               |
| Pydantic / redis-om model changes | Breaking schema changes (removed or renamed fields) that would invalidate existing Redis data; missing `index=True` on fields used in queries; `PrimaryKey` changes that break key lookup     |
| Backend abstraction compliance    | New or modified cloud backends implement all abstract methods from `BaseBackend`; runner lifecycle methods (create/delete/update) handle partial failures; no credentials or tokens hardcoded |
| Type hints                        | New functions and methods have type annotations (pyright is enforced); avoid `Any` unless unavoidable; use `Optional[X]` or `X \| None` consistently                                          |
| Exception handling                | No bare `except:`; catch specific exception types; cloud SDK exceptions wrapped with context before re-raising                                                                                |
| Dependency management             | `pyproject.toml` changes have a matching `poetry.lock` update; no version pins removed without justification                                                                                  |
| RQ job patterns                   | Jobs are idempotent (safe to retry); long-running jobs handle cancellation; job timeouts set appropriately                                                                                    |
| GitHub webhook handling           | Webhook signature validation not bypassed; event payload fields accessed safely (use `.get()` or model validation); state transitions in `workflow_job` events handled correctly              |
| Security                          | No credentials, tokens, or keys in plain text; no new `# type: ignore` that masks a real type error; no `shell=True` in subprocess calls                                                      |
| Breaking changes                  | Public API route changes (path, method, request/response schema); `Settings` model changes that break existing deployments; runner group config schema changes                                |
| Tests                             | New backend logic or job logic has corresponding unit tests; API-level changes covered by `tests/api/`; fixtures properly clean up Redis state                                                |

1. **Deliver your review:**

### If CI mode: post to GitHub

#### Part A: Inline file comments

For each specific issue, post a comment on the exact file and line:

```bash
gh api -X POST -H "Accept: application/vnd.github+json" "repos/<owner/repo>/pulls/<number>/comments" -f body="Your comment<br><br>— Claude Code" -f path="path/to/file" -F line=<line_number> -f side="RIGHT" -f commit_id="<headRefOid>"
```

**The command must stay on a single bash line.** Never use newlines in bash commands — use `<br>` for line breaks in comment bodies. Never put `<br>` inside code blocks or suggestion blocks.

Each inline comment must:

- Be short and direct — say what's wrong, why it's wrong, and how to fix it in 1-3 sentences
- No filler, no complex words, no long explanations
- When the fix is a concrete line change (not architectural), include a GitHub suggestion block so the author can apply it in one click:
  ````markdown
  ```suggestion
  corrected-line-here
  ```
  ````
  Only suggest when you can show the exact replacement. For architectural or design issues, just describe the problem.
  Example with a suggestion block:
  ````bash
  gh api ... -f body=$'Missing the shared-guidelines update command.<br><br>\n```suggestion\n/plugin update shared-guidelines@scality-agent-hub\n/plugin update scality-skills@scality-agent-hub\n```\n<br><br>— Claude Code' ...
  ````
- When the comment contains a suggestion block, use `$'...'` quoting with `\n` for code fence boundaries. Escape single quotes as `\'` (e.g., `don\'t`)
- End with: `— Claude Code`

Use the line number from the **new version** of the file (the line number you'd see after the PR is merged), which corresponds to the `line` parameter in the GitHub API.

#### Part B: Summary comment

```bash
gh pr comment <number> --repo <owner/repo> --body "LGTM<br><br>Review by Claude Code"
```

**The command must stay on a single bash line.** Never use newlines in bash commands — use `<br>` for line breaks in comment bodies.

Do not describe or summarize the PR. For each issue, state the problem on one line, then list one or more suggestions below it:

```markdown
- <issue>
  - <suggestion>
  - <suggestion>
```

If no issues: just say "LGTM". End with: `Review by Claude Code`

### If local mode: output the review as text

Do NOT post anything to GitHub. Instead, output the review directly as text.

For each issue found, output:

```markdown
**<file_path>:<line_number>** — <what's wrong and how to fix it>
```

When the fix is a concrete line change, include a fenced code block showing the suggested replacement.

At the end, output a summary section listing all issues. If no issues: just say "LGTM".

End with: `Review by Claude Code`

## What NOT to do

- Do not comment on markdown formatting preferences
- Do not suggest refactors unrelated to the PR's purpose
- Do not praise code — only flag problems or stay silent
- If no issues are found, post only a summary saying "LGTM"
- Do not flag style issues already covered by the project's linter (ruff, black, pyright)
