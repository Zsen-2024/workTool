# WorkTool

Windows 桌面小工具箱，把日常开发、办公中常用的小功能集中在一个窗口里，开箱即用。

基于 **Python 3 + PyQt5** 构建，采用插件式架构，左侧切换工具、右侧工作区操作，界面为浅色办公风格。

## 功能概览

| 工具 | 说明 |
|------|------|
| **AIHOT 资讯** | 获取 [AIHOT](https://aihot.virxact.com/) 精选 AI 新闻、热点榜与日报，Markdown 渲染展示 |
| **网址检索** | 检索本机 Chrome / Edge 浏览历史与书签（只读本地数据）；输入即搜，留空可浏览全部；单击打开，右键复制 URL |
| **接口调试** | 发送 HTTP/HTTPS 请求，查看响应（类似轻量 Postman） |
| **Markdown 预览** | 左侧编辑 Markdown 源码，右侧实时渲染预览 |
| **JSON 格式化** | JSON 美化、压缩、校验，支持复制、粘贴、打开文件 |

## 适用场景

- 日常接口联调、JSON 查看与格式化
- 快速预览 Markdown 文档
- 在本机浏览器历史/书签里找常用网址
- 浏览 AI 行业资讯简报
- 打包成单文件 `exe` 分发给同事，无需对方安装 Python

## 环境要求

| 项目 | 要求 |
|------|------|
| 开发 / 源码运行 | Windows 10 / 11（64 位），Python 3.10+（推荐 3.12） |
| 使用打包版 exe | Windows 10 / 11（64 位） |

## 快速开始

### 1. 安装依赖

```powershell
cd d:\WorkSpace\workTool
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 启动

```powershell
python main.py
```

### 3. 打包为 exe（可选）

```powershell
python -m PyInstaller build.spec --noconfirm
```

产物路径：`dist\WorkTool.exe`

更详细的开发、打包与同事分发说明见 [docs/使用与打包指南.md](docs/使用与打包指南.md)。

## 项目结构

```
workTool/
├── main.py              # 程序入口
├── build.spec           # PyInstaller 打包配置
├── requirements.txt     # Python 依赖
├── app/
│   ├── main_window.py   # 主窗口
│   ├── sidebar.py       # 左侧工具栏
│   ├── theme.py         # 全局样式
│   ├── tools/           # 各工具插件（继承 BaseToolWidget）
│   └── widgets/         # 共享 UI 组件
├── assets/              # 图标等资源
├── docs/                # 使用与打包文档
└── scripts/             # 辅助脚本
```

## 扩展新工具

1. 在 `app/tools/<工具名>/widget.py` 中继承 `BaseToolWidget`
2. 实现 `tool_id`、`tool_name` 与 UI 逻辑
3. 在 `app/tools/registry.py` 的 `_TOOLS` 列表中注册

重启应用后，新工具会出现在左侧工具箱中。

## 说明与限制

- **网址检索** 仅读取本地 Chrome / Edge 的 History / Bookmarks，无法获取浏览器当前打开的标签页；浏览器运行时数据库可能被占用，导致读不全
- **打包 exe** 基于 Python 3.12，不支持 Windows 7 / 8

## License

暂未指定开源协议，如需二次分发请先与作者确认。
