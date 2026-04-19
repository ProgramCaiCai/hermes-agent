# Semantic Patch Sync Implementation Plan

## Execution Status (2026-04-19)

- Workspace: `rebuild/main-20260419-semantic` is a clean rebuild branch on top of `original@957ca79e`
- `/spawn` semantic restore: implemented and verified by `tests/gateway/test_spawn_command.py` (`10 passed`)
- `archive/runtime-fixes`: treated as absorbed after targeted verification and archived
  - `tests/run_agent/test_run_agent_codex_responses.py` (`44 passed`)
  - `tests/gateway/test_session_race_guard.py` (`16 passed`)
  - `tests/gateway/test_api_server.py` (`114 passed`)
  - `tests/gateway/test_telegram_network.py` (`45 passed`)
- `archive/custom-api-mode`: treated as absorbed after targeted verification and archived
  - `tests/hermes_cli/test_model_provider_persistence.py` (`10 passed`)
  - `tests/hermes_cli/test_runtime_provider_resolution.py` (`67 passed`)
  - `tests/agent/test_auxiliary_client.py` (`71 passed`)
  - `tests/tools/test_delegate.py` (`67 passed`)
- Remaining work: replace the old mechanical sync doc with the semantic governance doc and propagate that policy to `patch/docs-sync-workflow`

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the fork on top of `original@957ca79e` by preserving only the still-needed semantics from the absorbed archived branches plus the active `patch/spawn-session` and `patch/docs-sync-workflow` branches.

**Architecture:** Use a fresh `rebuild/main-20260419-semantic` worktree as the sole implementation target. Treat patch branches as behavior references only. Re-add missing semantics with focused tests, then rewrite sync documentation so future maintenance uses semantic inventory + verification instead of ordered mechanical merges.

**Tech Stack:** Python, pytest, git worktrees, YAML-backed docs

---

### Task 1: Stabilize The Semantic Rebuild Workspace

**Files:**
- Modify: `docs/plans/2026-04-19-semantic-patch-sync-design.md`
- Modify: `docs/plans/2026-04-19-semantic-patch-sync.md`

**Step 1: Verify the new worktree starts from clean `original`**

Run: `git status --short --branch`
Expected: only the two new plan/design docs are untracked or staged; no merge state.

**Step 2: Record the semantic inventory as the source of truth**

Confirm the design doc lists:
- the four patch branches
- intended behaviors
- absorbed/partial/missing status
- migration rule: no more mechanical merge as the default workflow

**Step 3: Keep the old conflicted rebuild out of scope**

Do not continue `rebuild/main-20260419-957ca79e`.
Treat it as abandoned conflict exploration, not the implementation base.

### Task 2: Reconstruct `/spawn` As A Real User-Facing Feature

**Files:**
- Modify: `hermes_cli/commands.py`
- Modify: `gateway/run.py`
- Modify: `gateway/platforms/base.py` if active-session bypass needs adapter-level support
- Modify: `hermes_state.py` if session cloning/durable lineage metadata needs repair
- Test: `tests/gateway/test_spawn_command.py`
- Test: `tests/cli/test_branch_command.py` or a more appropriate CLI-facing test file if the current upstream layout differs

**Step 1: Write the failing tests**

Add focused tests that prove:
- `/spawn` is registered as a real slash command
- `/spawn` dispatches through gateway command routing
- `/spawn` works while the parent session is active/busy
- child results are delivered back durably to the parent flow

**Step 2: Run the focused tests to verify they fail**

Run: `python -m pytest -o addopts='' tests/gateway/test_spawn_command.py -q`
Expected: FAIL because upstream currently lacks complete `/spawn` exposure and/or durability guarantees.

**Step 3: Implement the smallest correct semantic restore**

Restore the user-visible `/spawn` behavior without replaying unrelated historical structure.

**Step 4: Run the focused tests again**

Run: `python -m pytest -o addopts='' tests/gateway/test_spawn_command.py -q`
Expected: PASS.

### Task 3: Re-check Runtime Fixes Against Current Upstream

**Files:**
- Modify only if needed:
  - `run_agent.py`
  - `gateway/run.py`
  - `gateway/platforms/api_server.py`
  - `gateway/platforms/telegram_network.py`
  - `hermes_cli/banner.py`
- Test:
  - `tests/run_agent/test_run_agent_codex_responses.py`
  - `tests/gateway/test_session_race_guard.py`
  - `tests/gateway/test_api_server.py`
  - `tests/gateway/test_telegram_network.py`
  - `tests/hermes_cli/test_banner_update_check.py` if absent, add it

**Step 1: Write or restore the missing regression tests**

Cover only the behaviors that remain semantically required:
- Responses replay/input validation
- hard `/stop` session unlock semantics
- local Codex SSE fallback timeout behavior
- Telegram proxy typing fix
- update-check cache scoping per repository/runtime

**Step 2: Run the focused runtime regression suite**

Run:
- `python -m pytest -o addopts='' tests/run_agent/test_run_agent_codex_responses.py -q`
- `python -m pytest -o addopts='' tests/gateway/test_session_race_guard.py -q`
- `python -m pytest -o addopts='' tests/gateway/test_api_server.py -q`
- `python -m pytest -o addopts='' tests/gateway/test_telegram_network.py -q`

Expected: identify exactly which semantics are still missing on current upstream.

**Step 3: Implement only confirmed gaps**

Do not restore every old patch hunk.
If a behavior already passes on current upstream, leave the code alone.

**Step 4: Re-run the same targeted suite**

Expected: PASS for the kept runtime semantics.

### Task 4: Verify `custom api_mode` Is Still Absorbed

**Files:**
- Modify only if a real regression appears:
  - `hermes_cli/main.py`
  - `agent/auxiliary_client.py`
  - `tools/delegate_tool.py`
  - `gateway/run.py`
- Test:
  - `tests/hermes_cli/test_model_provider_persistence.py`
  - `tests/hermes_cli/test_runtime_provider_resolution.py`
  - `tests/agent/test_auxiliary_client.py`
  - `tests/tools/test_delegate.py`

**Step 1: Run focused existing regressions**

Run:
- `python -m pytest -o addopts='' tests/hermes_cli/test_model_provider_persistence.py -q`
- `python -m pytest -o addopts='' tests/hermes_cli/test_runtime_provider_resolution.py -q`
- `python -m pytest -o addopts='' tests/agent/test_auxiliary_client.py -q`
- `python -m pytest -o addopts='' tests/tools/test_delegate.py -q`

**Step 2: Only patch genuine failures**

If upstream already satisfies the semantic contract, record that the patch is absorbed and leave the implementation untouched.

**Step 3: Re-run the same suite if changes were required**

Expected: PASS.

### Task 5: Rewrite Fork Sync Documentation To Semantic Workflow

**Files:**
- Modify: `docs/fork-patch-sync-workflow.md`
- Modify: `docs/plans/2026-04-19-semantic-patch-sync-design.md`
- Modify: `docs/plans/2026-04-19-semantic-patch-sync.md`

**Step 1: Replace mechanical-merge language**

Rewrite the doc so it no longer instructs:
- fixed-order `git merge --no-ff patch/*` as the default sync path
- treating `patch/*` as merge-ready textual diffs

**Step 2: Document semantic sync**

Add the canonical workflow:
- fast-forward `original`
- inspect semantic inventory
- rebuild a clean `rebuild/main-*`
- implement only still-missing fork semantics
- verify
- then update `main`

**Step 3: Define patch-branch migration rules**

Document that after this rebuild:
- `patch/*` branches become semantic ownership branches
- absorbed patches should shrink or freeze
- `patch/docs-sync-workflow` becomes the governance branch for semantic sync

### Task 6: Final Verification For The Semantic Rebuild

**Files:**
- Verify the files touched above

**Step 1: Run the minimum required fork verification**

Run:
- `python -m pytest -o addopts='' tests/run_agent/test_run_agent_codex_responses.py -q`
- `python -m pytest -o addopts='' tests/gateway/test_spawn_command.py -q`
- `python -m pytest -o addopts='' tests/gateway/test_session_race_guard.py -q`
- `python -m pytest -o addopts='' tests/hermes_cli/test_runtime_provider_resolution.py -q`

**Step 2: Run the document-mandated regression safety net**

Run:
- `python -m pytest -o addopts='' tests/hermes_cli/test_gateway_service.py -q`

**Step 3: Capture the actual state honestly**

Record:
- which old patch semantics are now absorbed upstream
- which were re-implemented on the semantic rebuild branch
- whether any required verification could not be run

### Task 7: Post-Rebuild Branch Governance Update

**Files:**
- Modify: `docs/fork-patch-sync-workflow.md`
- Potential follow-up branch operations on:
  - `archive/runtime-fixes`
  - `archive/custom-api-mode`
  - `patch/spawn-session`
  - `patch/docs-sync-workflow`

**Step 1: Define the follow-up branch policy**

State explicitly:
- `archive/custom-api-mode` is absorbed and should stay archived unless a future regression requires a new active patch branch
- `patch/spawn-session` remains a living semantic branch until upstream fully exposes/tests `/spawn`
- `archive/runtime-fixes` is absorbed and should stay archived unless a future regression requires a new active patch branch
- `patch/docs-sync-workflow` owns the semantic maintenance policy

**Step 2: Do not treat historical cherry-picks as sacred**

Only keep branch history/content that still maps to live fork behavior.
