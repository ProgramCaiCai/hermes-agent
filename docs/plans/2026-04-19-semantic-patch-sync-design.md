# Semantic Patch Sync Design

## 背景

fork 之前依赖固定顺序的机械合并：

- `patch/runtime-fixes`
- `patch/custom-api-mode`
- `patch/spawn-session`
- `patch/docs-sync-workflow`

当上游 `original` 从 `ac80bd61` 快进到 `957ca79e` 后，这套做法开始在 `gateway/run.py`、`run_agent.py`、测试和周边基础设施上产生大面积结构冲突。继续机械 replay 老 patch，只会把旧实现细节重新带回来，而不是保留 fork 真正还需要的行为差异。

## 决策

- 停止把 `patch/* -> merge --no-ff -> main` 当作默认同步路径。
- 把每个 `patch/*` 分支视为“语义来源”，而不是“文本补丁来源”。
- 以干净的 `original@957ca79e` 新建 `rebuild/main-20260419-semantic`，只重建仍然缺失的 fork 语义。
- 将 `patch/docs-sync-workflow` 重写为语义同步治理分支，废弃固定顺序机械 merge 说明。
- rebuild 稳定后，逐步收缩 `patch/*`，让它们只承载仍未被上游吸收的真实 fork 行为。

## 已验证的语义盘点

### `patch/runtime-fixes`

原始意图：

- 加固 Responses API 转换与 replay 校验
- 修复 `/stop` 会话解锁与网关竞态
- 兜底 Codex/Responses 流式回退
- 修复 Telegram 代理相关行为
- 维持 API server 与运行时稳定性

2026-04-19 定向验证结果：

- `tests/run_agent/test_run_agent_codex_responses.py`: 44 passed
- `tests/gateway/test_session_race_guard.py`: 16 passed
- `tests/gateway/test_api_server.py`: 114 passed
- `tests/gateway/test_telegram_network.py`: 45 passed

结论：

- 当前 upstream 已经吸收了这条 patch 的主要语义。
- rebuild 分支不需要回放旧实现。
- 后续只在出现新的定向失败时，按失败点最小补洞。

### `patch/custom-api-mode`

原始意图：

- 显式保留并传播自定义 provider 的 `api_mode`
- 避免被隐式推断或默认值覆盖
- 把 `api_mode` 继续传到 auxiliary、gateway runtime、delegate child agent

2026-04-19 定向验证结果：

- `tests/hermes_cli/test_model_provider_persistence.py`: 10 passed
- `tests/hermes_cli/test_runtime_provider_resolution.py`: 67 passed
- `tests/agent/test_auxiliary_client.py`: 71 passed
- `tests/tools/test_delegate.py`: 67 passed

结论：

- 当前 upstream 已基本吸收该 patch 语义。
- rebuild 分支不需要重新实现旧 patch。
- 后续将其降级为“回归监控语义”，而不是长期复制代码。

### `patch/spawn-session`

原始意图：

- 暴露真实可用的 `/spawn`
- 从父会话克隆上下文到子会话
- 即使父会话忙碌，也允许 `/spawn` 直通
- 子任务完成后把结果稳定回写到父上下文

2026-04-19 rebuild 实施结果：

- 已恢复 `/spawn` 命令注册
- 已恢复运行中会话与 adapter active-session 场景下的 `/spawn` 直通
- 已增加 `SessionDB.clone_session()`
- 已恢复子会话后台执行、父会话 transcript 镜像回写、媒体结果回传
- `tests/gateway/test_spawn_command.py`: 10 passed

结论：

- 这是当前唯一确认仍需保留的活跃 fork 语义。
- `patch/spawn-session` 应从“历史补丁堆”收缩为“/spawn 语义所有权分支”。

### `patch/docs-sync-workflow`

原始意图：

- 记录 fork 维护流程、worktree 规则、安装目录同步规则

当前语义定位：

- 不属于上游吸收范围
- 现在负责维护“语义同步”治理，而不是“固定顺序 merge patch”

结论：

- 该分支继续保留，但职责改为 fork 治理文档。

## 目标状态

1. `rebuild/main-20260419-semantic` 基于干净 `original@957ca79e`
2. 只保留仍缺失的 `/spawn` 语义
3. `runtime-fixes` 与 `custom-api-mode` 以验证为主，不再机械重放
4. `docs/fork-patch-sync-workflow.md` 成为语义同步的正式工作流文档
5. `patch/*` 分支不再被视为固定顺序 merge 的文本差异集合

## 验收标准

- rebuild 分支不是冲突修补树，而是干净基线上语义重建
- `/spawn` 对用户可见、可执行、可回写，且有回归测试
- runtime 与 custom-api-mode 通过定向验证后不做无意义重放
- `patch/docs-sync-workflow` 明确接管语义同步治理
