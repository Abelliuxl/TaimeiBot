---
name: wow_version_check
description: 查询当前魔兽世界正式服版本号。当用户问到版本、更新、资料片等时使用。注意：地心之战(The War Within)是11.0，至暗之夜(The Midnight)是12.0，不要混淆。
workflow: |
  1. 先用 read_memory 查看记忆中已有的版本信息
  2. 用 fetch_url 获取 https://wow.blizzard.cn/news/ 查看最新公告中的版本号（这是国服官网，最可靠）
  3. 再用 tavily_search 或 brave_search 搜索"魔兽世界 12.0 至暗之夜 当前版本"交叉验证
  4. 如果官网获取失败，打开搜索结果中 wow.blizzard.cn 或权威 wow 媒体的链接确认
  5. 确认版本号后，用 update_memory 把当前版本号更新到 Key Facts & Decisions 章节（replace 模式覆盖旧记录）
  6. 回复时明确告诉用户当前版本号
---
