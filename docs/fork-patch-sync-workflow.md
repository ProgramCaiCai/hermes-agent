# Fork Patch 同步流程

本文档描述本 fork 的长期维护方式。

目标分支结构：

- `original`：严格对齐官方上游 `origin/main`
- `patch/runtime-fixes`：运行时与兼容性补丁
- `patch/custom-api-mode`：自定义 provider / `api_mode` 补丁
- `patch/spawn-session`：`/spawn` 会话补丁
- `patch/docs-sync-workflow`：fork 维护文档与同步流程约定
- `main`：发布用整合分支，只承载 `original + patch/*` 的合成结果

原则：

1. 不直接在 `original` 上开发
2. 不把长期改动直接堆在 `main`
3. 所有 fork 定制能力都尽量收敛到 `patch/*`
4. `main` 可以重建，可以用 `--force-with-lease` 更新
5. 开发目录与运行目录必须分离
6. 正式版本只发布到 `~/.hermes/hermes-agent`

## 一次性认知

- 真正需要长期维护的是 `patch/*`
- `original` 只是官方镜像
- `main` 只是“当前发布版”
- 如果以后新增功能，优先新建独立 `patch/<topic>`，不要继续往已有 patch 里乱塞

## 日常同步流程

以下命令默认在仓库根目录执行。

### 1. 更新官方基线

```bash
git fetch origin
git switch original
git merge --ff-only origin/main
git push fork original
```

要求：

- `original` 不允许有本地私有提交
- `merge --ff-only` 失败时，先检查是不是有人误改了 `original`

### 2. 从最新 `original` 重建新的集成分支

建议每次同步都新起一个临时整合分支，不直接在旧 `main` 上硬 merge。

当前固定合并顺序：

1. `patch/runtime-fixes`
2. `patch/custom-api-mode`
3. `patch/spawn-session`
4. `patch/docs-sync-workflow`

这四个 patch 以后按上面顺序合并，不临时改顺序。

```bash
git switch -C rebuild/main-$(date +%Y%m%d) original
git merge --no-ff patch/runtime-fixes -m "merge(patch): integrate runtime fixes"
git merge --no-ff patch/custom-api-mode -m "merge(patch): integrate custom api mode"
git merge --no-ff patch/spawn-session -m "merge(patch): integrate spawn session"
git merge --no-ff patch/docs-sync-workflow -m "merge(patch): integrate docs sync workflow"
```

如果以后增加新的 patch，就继续按固定顺序往下 merge。

建议：

- 先 merge 更底层、更通用的 patch
- 再 merge 更偏功能性的 patch
- 顺序一旦稳定下来，后面尽量不要频繁改

## 冲突处理原则

处理冲突时遵循这三个优先级：

1. 保留上游最新结构
2. 只补回本 fork 真正需要的行为差异
3. 能缩小 patch 范围就缩小，不要把已被上游吸收的逻辑重新带回来

尤其是 `patch/custom-api-mode`：

- 上游已经吸收的 `api_mode` 传递链路不要重复背
- 只保留 custom provider / delegation / 剩余缺口修复

## 验证

整合完成后，至少做定向验证，再决定是否替换 `main`。

示例：

```bash
python -m pytest -o addopts='' tests/run_agent/test_run_agent_codex_responses.py -q
python -m pytest -o addopts='' tests/gateway/test_spawn_command.py -q
python -m pytest -o addopts='' tests/hermes_cli/test_gateway_service.py -q
```

如果当前环境缺依赖或 Python 版本不满足要求，需要在发布说明里明确写出，不能假装验证通过。

## 替换 main

确认新整合分支可接受后，用它覆盖 `main`。

```bash
git branch -f main HEAD
git switch main
git push --force-with-lease fork main
```

或者直接：

```bash
git push --force-with-lease fork HEAD:main
```

说明：

- `main` 是可重建产物，不是补丁真源
- 覆盖 `main` 前，建议先给旧远端 `main` 打一个 backup 分支

示例：

```bash
git fetch fork main
git push fork fork/main:refs/heads/backup/remote-main-before-sync-$(date +%Y%m%d)
git push --force-with-lease fork HEAD:main
```

## 新增补丁的方式

新增 fork 私有能力时，不要直接改 `main`，而是：

```bash
git switch -c patch/<topic> original
```

然后在这个 patch 分支上独立开发、提交、验证。

等 patch 稳定后，再把它加入日常整合顺序。

## 不建议的做法

不要这样做：

- 直接在 `original` 上改代码
- 直接在 `main` 上堆长期提交
- 把多个无关改动混进同一个 patch 分支
- 为了省事，把上游已经修掉的逻辑继续整包保留
- 未验证就覆盖远端 `main`

## 建议的实际工作区布局

- 当前日常开发目录可以保留为 `wip/*`
- `original`、`patch/*`、`main` 最好各自放在独立 worktree
- 冲突解决和整合发布优先在干净 worktree 中完成

## 运行与发布约定

- 开发环境与运行环境分离，不直接用开发 worktree 挂生产网关
- fork 的正式发布目录固定为 `~/.hermes/hermes-agent`
- 本地网关服务应从 `~/.hermes/hermes-agent` 版本启动
- 开发 worktree 只用于开发、验证、重建 `main`
- 验证通过后的正式版本，再同步到 `~/.hermes/hermes-agent`

推荐流程：

1. 在开发 worktree 中完成 patch 更新与 `main` 重建
2. 在开发 worktree 中完成定向回归验证
3. 将确认通过的正式版本同步到 `~/.hermes/hermes-agent`
4. 用 `~/.hermes/hermes-agent` 版本刷新本地 gateway service

## 安装目录同步规则

- `~/.hermes/hermes-agent` 是运行目录，不是开发目录
- 安装目录默认不保留脏改动；需要保留的内容应先转移到开发目录
- 安装目录内的 `venv` 需要保留，不随代码同步一起删除
- 安装目录的正式同步源使用 fork 远端，即 `programcaicai/*`

推荐同步步骤：

```bash
git fetch programcaicai
git branch -f original programcaicai/original
git branch -f patch/runtime-fixes programcaicai/patch/runtime-fixes
git branch -f patch/custom-api-mode programcaicai/patch/custom-api-mode
git branch -f patch/spawn-session programcaicai/patch/spawn-session
git branch -f patch/docs-sync-workflow programcaicai/patch/docs-sync-workflow
git switch main
git reset --hard programcaicai/main
git branch --set-upstream-to=programcaicai/main main
```

如果需要清理安装目录中的临时文件，只清理代码产物，不删除 `venv`。

## 本 fork 当前约定

当前长期维护的 patch 分支：

- `patch/runtime-fixes`
- `patch/custom-api-mode`
- `patch/spawn-session`
- `patch/docs-sync-workflow`

当前不纳入 patch 体系的本地临时改动：

- Codex auth 同步修正相关脏改动

如果未来这些临时改动也要长期保留，应该单独拆成新的 `patch/<topic>`，不要直接留在工作目录里。
