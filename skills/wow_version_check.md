---
name: wow_version_check
description: 查询当前魔兽世界版本信息。当用户问到版本相关问题时使用此技能。
workflow: |
  1. 使用 tavily_search 或 brave_search 搜索"魔兽世界 当前版本 2026"
  2. 用 browse_webpage 打开搜索结果中官网或权威来源的链接确认版本号
  3. 对比用户提到的版本号与当前版本是否一致
  4. 通过 update_memory 把当前版本号记入 Key Facts & Decisions
---
