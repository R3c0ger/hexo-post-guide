# Post Guide for Hexo

我不知道该起啥名字了，毕竟这个项目只是为了满足我的个人需求而已。
I don't know what to name this project, after all, it's just for my personal needs.

欢迎为本项目提供更多的功能，或者提出更好的建议。未来可能会添加 GUI 界面，或者将该项目的需求改造为 Hexo 插件。但我现在还不会写插件。
Feel free to contribute more features to this project, or suggest better ideas. In the future, a GUI interface may be added, or the requirements of this project may be transformed into a Hexo plugin. But I don't know how to write plugins yet.

## Usage

```shell
usage: post-guide.py [-h] [-n NEW [NEW ...] | -f | -r | -s | -p | -rs | -sp | -ps | -rps | -rsp | -d]

Hexo Blog Management Tool

optional arguments:
  -h, --help            show this help message and exit
  -n NEW [NEW ...], --new NEW [NEW ...]
                        Create a new draft with the given title (hexo new post "<title>"), and move it to _draft
  -f, --finalize        Finalize all drafts, move them to source/_posts and modify the content
  -r, --refresh         Refresh Hexo (hexo clean && hexo generate)
  -s, --start           Start Hexo server (hexo server)
  -p, --preview         Preview the blog (start http://localhost:4000)
  -rs, --refresh_start  Refresh and start Hexo server (hexo clean && hexo generate && hexo server)
  -sp, --start_preview  Start server and preview the blog (start http://localhost:4000 && hexo server)
  -ps, --preview_start  Start server and preview the blog (start http://localhost:4000 && hexo server)
  -rps, --refresh_preview_start
                        Refresh, preview and start server (hexo clean && hexo g && start http://localhost:4000 && hexo s)
  -rsp, --refresh_start_preview
                        Refresh, preview and start server (hexo clean && hexo g && start http://localhost:4000 && hexo s)
  -d, --deploy          Deploy the blog (hexo deploy)
```

## Installation

本脚本依赖于 Python 3，不依赖任何第三方库，所以只需要安装 Python 3、下载 post-guide.py（和 post-guide.bat）并运行即可。
This script depends on Python 3, and does not depend on any third-party libraries, so you only need to install Python 3, download post-guide.py (and post-guide.bat) and run it.

## License

本项目使用 MIT 协议，详细内容请查看 [LICENSE](LICENSE) 文件。
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.