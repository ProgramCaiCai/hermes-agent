# Fork Patch 语义同步流程

本文档定义本 fork 的默认同步方式。默认采用全托管语义同步，不再采用固定顺序机械 merge `patch/*`。

## 分支职责

- `original`：严格对齐官方上游，只允许 `ff-only`
- `rebuild/main-*`：每次同步时从最新 `original` 新建的语义重建分支
- `main`：当前发布分支，是可重建产物，不是补丁真源
- `archive/runtime-fixes`：已归档的运行时补丁分支，仅保留历史参考，不参与默认同步
- `archive/custom-api-mode`：已归档的 `api_mode` 补丁分支，仅保留历史参考，不参与默认同步
- `patch/spawn-session`：`/spawn` 语义所有权分支；当前仍是活跃 fork 能力
- `patch/docs-sync-workflow`：fork 治理与同步规则分支

## 默认原则

- 不直接在 `original` 上开发
- 不再把 `patch/*` 当作 merge-ready 文本补丁串
- 不再维护固定 merge 顺序作为默认同步路径
- 只保留仍然缺失的 fork 语义，不回放已被 upstream 吸收的旧实现
- 先验证，再声明 patch 仍然有效
- `main` 可以被新的 `rebuild/main-*` 覆盖，但覆盖前必须完成定向验证

## 语义同步步骤

### 1. 更新上游基线

```bash
git fetch origin
git switch original
git merge --ff-only origin/main
git push fork original
```

要求：

- `original` 不允许带私有提交
- 如果 `ff-only` 失败，先修正基线，而不是继续 patch 合并

### 2. 建立语义重建分支

```bash
git switch -C rebuild/main-$(date +%Y%m%d) original
```

说明：

- rebuild 分支必须从干净 `original` 起步
- 旧的冲突修补树不继续沿用

### 3. 盘点 patch 语义，而不是机械合并 patch

同步前先回答四个问题：

1. 这个 patch 的原始行为是什么
2. 当前 upstream 是否已吸收
3. 如果只吸收了一部分，剩余缺口是什么
4. 这些缺口有没有现成测试或可写成定向回归

当前基线结论：

- `archive/runtime-fixes`：已被 upstream 大体吸收，作为归档分支保留
- `archive/custom-api-mode`：已被 upstream 大体吸收，作为归档分支保留
- `patch/spawn-session`：仍需保留，当前 rebuild 已重建完整 `/spawn`
- `patch/docs-sync-workflow`：继续保留，负责维护本治理文档

### 4. 只实现真实缺口

不要默认执行：

```bash
git merge --no-ff patch/spawn-session
git merge --no-ff patch/docs-sync-workflow
```

这些命令也不是默认流程，只是说明当前仍活跃的 patch 分支范围。`archive/*` 不参与默认同步；默认做法仍然是直接在 `rebuild/main-*` 上按当前架构重实现缺口语义。

### 5. 做定向验证

本轮已验证的最小基线：

```bash
python -m pytest -o addopts='' tests/gateway/test_spawn_command.py -q
python -m pytest -o addopts='' tests/run_agent/test_run_agent_codex_responses.py -q
python -m pytest -o addopts='' tests/gateway/test_session_race_guard.py -q
python -m pytest -o addopts='' tests/gateway/test_api_server.py -q
python -m pytest -o addopts='' tests/gateway/test_telegram_network.py -q
python -m pytest -o addopts='' tests/hermes_cli/test_model_provider_persistence.py -q
python -m pytest -o addopts='' tests/hermes_cli/test_runtime_provider_resolution.py -q
python -m pytest -o addopts='' tests/agent/test_auxiliary_client.py -q
python -m pytest -o addopts='' tests/tools/test_delegate.py -q
```

如果验证失败：

- 只修复失败所指向的语义缺口
- 不允许借机整包回放旧 patch

### 6. 更新 `main`

当 rebuild 分支通过本轮所需验证后，再用它更新 `main`。

```bash
git branch -f main HEAD
git switch main
git push --force-with-lease fork main
```

说明：

- `main` 是发布产物，不是补丁真源
- 覆盖前建议先备份远端 `main`

## patch 分支治理规则

### `archive/runtime-fixes`

- 默认目标：历史归档
- 不再作为活跃 patch 参与同步
- 只有在确认需要“复活”为活跃差异时，才重新拆出新的 patch 分支

### `archive/custom-api-mode`

- 默认目标：历史归档
- 不再作为活跃 patch 参与同步
- 如果未来出现新的 `api_mode` 回归，应新建新的 patch 分支，而不是直接恢复 archive 分支

### `patch/spawn-session`

- 默认目标：保留 `/spawn` 活跃语义
- 只围绕 `/spawn` 命令注册、忙时直通、子会话执行、父会话回写这四类核心行为演进
- 不把无关能力塞进这个分支

### `patch/docs-sync-workflow`

- 默认目标：维护本治理文档和相关计划文档
- 负责定义“哪些 patch 仍然活着，哪些已经被吸收”
- 负责记录语义同步的验证门槛

## 不再允许的默认做法

- 把固定顺序 `merge --no-ff patch/*` 当成默认同步流程
- 为了省事保留已被 upstream 吸收的整块旧实现
- 先合并再验证
- 直接在旧 `main` 上硬修冲突
- 未验证就覆盖远端 `main`

## 开发目录与运行目录

- 开发 worktree 负责实现与验证
- 运行目录 `~/.hermes/hermes-agent` 只承载已确认的发布结果
- 不直接在运行目录里做长期开发
- 安装目录需要保留 `venv`

## 当前结论

- 语义重建分支：`rebuild/main-20260419-semantic`
- 当前确认需保留的活跃 fork 语义：`/spawn`
- 当前确认已归档的吸收语义：`archive/runtime-fixes`、`archive/custom-api-mode`
- 当前治理分支：`patch/docs-sync-workflow`
