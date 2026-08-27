# WorkTool MVP 设计规格

## 目标

Windows 桌面小工具箱，MVP 首个工具为 JSON 格式化，验证技术栈与扩展架构后可逐步增加工具。

## 需求摘要

| 类别 | 内容 |
|------|------|
| 平台 | Windows，打包为单文件 exe |
| 技术栈 | Python 3.10+、PyQt5、PyInstaller |
| 布局 | 左侧工具栏（约 200px）+ 右侧工作区 |
| 主题 | 浅色办公风（#F5F6F8 背景、#1677FF 主色） |
| JSON 能力 | 格式化、压缩、校验、复制/清空、剪贴板粘贴、文件导入 |

## 架构

- `BaseToolWidget` 基类 + 注册表，新工具实现基类并注册即可
- 主窗口：`Sidebar` + `QStackedWidget` 切换工具页
- JSON 处理使用标准库 `json`，缩进 2 空格

## MVP 范围外

多主题、JSON 树视图、自动更新、安装程序。
