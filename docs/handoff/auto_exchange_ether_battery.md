# 自动兑换以太电池交接文档

更新时间：2026-06-08

## 用途

这份文档给其他电脑上的 agent 用于部署、验证或继续维护“体力计划自动兑换以太电池”版本。

本文档所在分支是专门的交接分支，不用于上游 PR：

- 交接分支：`pumpkinperson996/origin-fork:handoff/auto-exchange-ether-battery`
- PR 分支：`pumpkinperson996/origin-fork:feature/auto-exchange-ether-battery`
- 上游 PR：`https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/pull/2299`
- 功能提交：`e9cd428 新增体力计划自动兑换以太电池`

`feature/auto-exchange-ether-battery` 是给上游 PR 用的干净分支，不包含本交接文档。
`handoff/auto-exchange-ether-battery` 包含同一份功能代码，并额外包含本文件，方便其他电脑部署时读取。

## 建议技能

- `github:github`：查看 PR、分支、CI 与评论状态。
- `github:gh-address-comments`：后续处理 PR review comment 时使用。
- `diagnose`：如果其他电脑部署后流程点击、OCR 或运行行为异常，用于复现和定位。

## 功能摘要

体力计划设置页新增开关：`自动兑换以太电池`。

开启后，体力计划启动时会先尝试执行：

```text
菜单 -> 仓库 -> 材料道具页 -> 点击左下角道具处理按钮 -> 查找以太电池 -> 以太电池合成页面 -> 最大数量合成
```

流程要点：

- 查找目标是 `以太电池`，不是 `储值电卡`。
- 合成需要消耗 `储值电卡`。
- 文案和术语使用“自然恢复的电量兑换为以太电池”，不要写成“储蓄电量兑换为以太电池”。
- 找不到以太电池、素材不足、确认失败或无法进入页面时，不阻断体力计划，会回到菜单继续原流程。
- 道具处理列表只向下滚动查找，最多 5 次。

## 关键文件

- `src/zzz_od/application/charge_plan/charge_plan_config.py`：新增 `auto_exchange_ether_battery` 配置项。
- `src/zzz_od/gui/view/one_dragon/charge_plan_interface.py`：新增设置页开关与说明文案。
- `src/zzz_od/application/charge_plan/charge_plan_app.py`：在识别电量前串入兑换流程。
- `src/zzz_od/operation/exchange_ether_battery.py`：新增自动兑换以太电池操作。
- `assets/game_data/screen_info/storage_material.yml`：仓库材料道具页与道具处理按钮。
- `assets/game_data/screen_info/item_processing*.yml`：道具处理、合成确认、获得弹窗画面定义。
- `assets/game_data/screen_info/_od_merged.yml`：合并后的画面配置。
- `docs/develop/zzz/application/charge_plan.md`：功能说明文档。

## 部署方式

如果目标电脑没有仓库，直接克隆交接分支：

```powershell
git clone -b handoff/auto-exchange-ether-battery https://github.com/pumpkinperson996/origin-fork.git C:\ZZZ-OD
cd C:\ZZZ-OD
.\.install\uv\uv.exe sync --group dev --group gamepad
.\.install\uv\uv.exe run --env-file .env src/zzz_od/gui/app.py
```

如果目标电脑已经有上游仓库：

```powershell
cd C:\ZZZ-OD
git remote add fork https://github.com/pumpkinperson996/origin-fork.git
git fetch fork handoff/auto-exchange-ether-battery
git switch -c handoff/auto-exchange-ether-battery fork/handoff/auto-exchange-ether-battery
.\.install\uv\uv.exe sync --group dev --group gamepad
.\.install\uv\uv.exe run --env-file .env src/zzz_od/gui/app.py
```

如果 `fork` 远端已经存在，跳过 `git remote add fork ...`。

如需部署不含交接文档的 PR 分支，把上面命令里的 `handoff/auto-exchange-ether-battery` 换成 `feature/auto-exchange-ether-battery`。

## 使用方式

启动 GUI 后：

1. 打开一条龙的体力计划设置页。
2. 开启 `自动兑换以太电池`。
3. 正常运行体力计划。

功能会在体力计划启动并进入菜单后尝试兑换一次，以后续体力计划流程为主。兑换失败时应跳过，不应导致体力计划整体停止。

## 验证记录

在原电脑上已经验证：

```powershell
.\.install\uv\uv.exe run ruff check src\zzz_od\application\charge_plan\charge_plan_app.py src\zzz_od\application\charge_plan\charge_plan_config.py src\zzz_od\gui\view\one_dragon\charge_plan_interface.py src\zzz_od\operation\exchange_ether_battery.py
```

结果：通过。

```powershell
.\.install\uv\uv.exe run pytest zzz-od-test\ -m "not requires_secrets"
```

结果：`32 passed, 10 deselected`。

完整测试中带 `requires_secrets` 的推送通道测试需要 `PUSH_*` 环境变量，普通部署环境没有这些密钥时会失败，这不是本功能导致的问题。

## 截图与调试

原电脑上用于定位页面的截图放在本地：

```text
C:\ZZZ-OD\.debug\exchange_ether_battery\
```

这些截图没有提交到仓库，也不应该进入上游 PR。若 reviewer 后续需要截图说明，先挑选关键截图作为 PR 评论附件，评论前给用户确认。

如果运行日志里出现大量 OCR 或 YAML 加载信息，优先检查应用是否开启了调试模式。这类全局日志不是本功能专门输出的内容。

## PR 协作注意事项

- PR #2299 当前不是 Draft。
- CodeRabbit 已经被触发并返回成功状态。
- 回复 review comment 前，先把拟回复内容给用户确认。
- 不要把本交接文档合入 PR 分支。
- 不要把本地 `.debug/` 截图、压缩包、日志或 `ZZZ-autorun/` 目录提交到上游 PR。
