from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS_PATH = ROOT / "AGENTS.md"
DOC_PATH = ROOT / "docs" / "fork-patch-sync-workflow.md"


def test_agents_declares_semantic_sync_as_default():
    text = AGENTS_PATH.read_text(encoding="utf-8")

    assert "semantic sync" in text
    assert "Do not use fixed-order `git merge --no-ff patch/*` as the standard sync workflow." in text
    assert "create a clean `rebuild/main-*` branch from the latest `original`" in text
    assert "`patch/docs-sync-workflow` owns this governance policy." in text


def test_fork_sync_doc_forbids_mechanical_merge_as_default():
    text = DOC_PATH.read_text(encoding="utf-8")

    assert "默认采用全托管语义同步" in text
    assert "不再采用固定顺序机械 merge `patch/*`" in text
    assert "这些命令不再是默认流程" in text
    assert "只修复失败所指向的语义缺口" in text
    assert "当前确认需保留的活跃 fork 语义：`/spawn`" in text
