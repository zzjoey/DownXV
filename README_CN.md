# DownXV

[![Release](https://github.com/zzjoey/DownXV/actions/workflows/release.yml/badge.svg)](https://github.com/zzjoey/DownXV/actions/workflows/release.yml)

[English](README.md)

一款免费、开源的 macOS 应用，用于下载 X（Twitter）推文中的视频。

**自动读取浏览器 Cookie，支持多视频推文，公开内容无需登录。**

| 1. 找到 X 上的推文 | 2. 在 DownXV 中粘贴链接 | 3. MP4 已保存 |
| :---: | :---: | :---: |
| <img src="assets/images/post.png" width="280" alt="X 推文" /> | <img src="assets/images/ui.png" width="280" alt="DownXV 应用" /> | <img src="assets/images/download.png" width="280" alt="保存的 MP4" /> |

## 功能

- **自动读取浏览器 Cookie** — 从 <img src="assets/icon-chrome.svg" width="16" height="16" alt="Chrome" /> Chrome、<img src="assets/icon-firefox.svg" width="16" height="16" alt="Firefox" /> Firefox 或 <img src="assets/icon-edge.svg" width="16" height="16" alt="Edge" /> Edge 读取 Cookie 以访问需要登录的内容，无需手动导出
- **多视频支持** — 自动下载推文中包含的所有视频
- **并发下载** — 最多同时下载 3 个任务，每个任务独立显示进度
- **画质选择** — 最佳画质、1080p、720p、480p 或仅音频
- **实时进度** — 显示下载速度、预计剩余时间、百分比和文件大小
- **自动合并为 MP4** — 自动合并视频流和音频流为单个 MP4 文件
- **点击即可查看** — 点击已完成的下载卡片，在 Finder 中显示文件
- **安全的临时文件清理** — 下载成功、失败、取消或关闭窗口时自动清理临时文件
- **原生 macOS 外观** — San Francisco 系统字体、透明标题栏、紫色主题的精致浅色界面

## 快速开始

### 从源码运行

```bash
git clone https://github.com/zzjoey/DownXV.git
cd DownXV
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

### 构建 macOS .dmg

```bash
./release.sh
```

DMG 文件将生成在 `dist/DownXV-<version>.dmg`。打开后将应用拖入 `/Applications` 即可安装。

## 使用方法

1. 粘贴 X/Twitter 推文链接
2. 选择保存目录、画质和 Cookie 来源
3. 点击 **Download Video**
4. 视频保存为 MP4 — 点击卡片即可在 Finder 中查看

> 大多数 X 视频需要登录才能访问。选择你的浏览器作为 Cookie 来源 — DownXV 会自动从已登录的浏览器会话中读取 Cookie。

## 技术栈

| 组件 | 用途 |
| --- | --- |
| **Python 3.10+** | 运行环境 |
| **PySide6** | Qt GUI 框架 |
| **yt-dlp** | 视频提取引擎 |
| **PyInstaller** | macOS .app 打包 |

## 项目结构

```
├── run.py                  # 入口文件
├── build.spec              # PyInstaller 配置
├── release.sh              # 构建 .app 并打包 .dmg
├── requirements.txt
├── assets/
│   ├── logo.png            # 应用图标
│   ├── icon-chrome.svg     # Cookie 选择器的浏览器图标
│   ├── icon-firefox.svg
│   ├── icon-edge.svg
│   ├── icon-none.svg
│   └── icon-github.svg
└── src/
    ├── app.py              # QApplication 启动
    ├── main_window.py      # 主窗口 UI + 下载任务管理
    ├── downloader.py       # yt-dlp 下载线程
    ├── url_validator.py    # X/Twitter URL 校验
    ├── styles.py           # QSS 样式表（浅色主题）
    └── logo.py             # 图标加载器
```

## 参与贡献

欢迎提交 Issue 和 Pull Request。

## 许可证

MIT
