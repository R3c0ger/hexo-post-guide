import os
import re
import shutil
import socket
from datetime import datetime
from pathlib import Path
from typing import Union


red     = lambda text: f"\033[31m{text}\033[0m"
green   = lambda text: f"\033[32m{text}\033[0m"
yellow  = lambda text: f"\033[33m{text}\033[0m"
blue    = lambda text: f"\033[34m{text}\033[0m"


def title2filename(title: str) -> str:
    """
    将文章标题转换为文件名，进行如下清理操作：
    Convert title to filename, while doing the following cleaning:

    1. 将一个或多个连续的空格、短横线或下划线替换为单个短横线
       Replace one or more consecutive spaces, hyphens, or underscores with a single hyphen
    2. 删除所有特殊符号 Remove all special characters
    3. 将所有字母转换为小写 Convert all letters to lowercase
    4. 检测转换后的文件名：
       如果超出64个字符，则进行警告；如果超出255个字符，则进行错误提示
       Detect the converted file name, 
       if it exceeds 64 characters, a warning will be issued;
       if it exceeds 255 characters, an error message will be issued
    
    例如：For example:
    M  an Sp_af-as--as__!@#$%^&*()=+`?/\|[]{}:";'<>?,./汉字【∏⒕あアΞVIIДó┒┃
    -> m-an-sp-af-as-as-汉字【∏⒕あアΞVIIДo┒┃.md

    Args:
        title: 文章标题 The title of the article

    Returns:
        filename: 文件名 The file name
    """
    print(green("\nOriginal:"), f"{title}")

    # 将一个或多个连续的空格、短横线或下划线替换为单个短横线
    filename = re.sub(r'[\s\-_]+', '-', title)
    # 删除所有非字母数字字符（保留汉字和其他非拉丁字符）
    filename = re.sub(r'[^\w\-]', '', filename, flags=re.UNICODE)
    # 将所有字母转换为小写
    filename = filename.lower()

    # 检测转换后的文件名长度
    if len(filename) > 255:
        raise ValueError(red(
            "The converted file name exceeds the "
            "maximum allowed length of 255 characters.")
        )
    elif len(filename) > 64:
        print(red("Warning:"), "The converted file name exceeds 64 characters.")

    print(green("Converted:"), f"{filename}")
    return filename


def exec_hexo_cmds(cmds: Union[list[str], str]):
    """
    执行 Hexo 命令，如提供多个命令，则按顺序执行
    Execute Hexo commands, if multiple commands are provided

    例如：For example:
        hexo_cmd(['new post "Hello World"']) # hexo new post "Hello World"
        hexo_cmd(['clean', 'g', 'd'])        # hexo clean && hexo g && hexo d

    Args:
        cmds: Hexo 命令或命令数组，元素为去掉 "hexo" 的命令字符串
              Hexo command string or array, elements are command strings without "hexo"
    """
    if isinstance(cmds, str):
        cmds = [cmds]
    hexo_path = 'hexo'
    for cmd in cmds:
        full_cmd = f'{hexo_path} {cmd}'
        print(blue("\nExecuting:"), f"{full_cmd}")
        try:
            os.system(full_cmd)
        except Exception as e:
            print(red("Error:"), e)


def check_get_make_dirs() -> tuple[Path, Path, Path, Path]:
    """
    检查并获取或创建所需目录
    Check and get or create the required directories
    """
    hexo_root = Path.cwd()
    source_posts_dir = hexo_root / 'source' / '_posts'
    # 若 source_posts_dir 不存在则说明当前目录不是 Hexo 根目录，报错
    if not source_posts_dir.exists():
        raise FileNotFoundError(red("Error:"), "Hexo root directory not found.")

    # 创建 _draft, _hidden, _archived 目录
    draft_dir = hexo_root / '_draft'
    hidden_dir = hexo_root / '_hidden'
    archived_dir = hexo_root / '_archived'
    draft_dir.mkdir(exist_ok=True)
    hidden_dir.mkdir(exist_ok=True)
    archived_dir.mkdir(exist_ok=True)
    return source_posts_dir, draft_dir, hidden_dir, archived_dir


def change_front_matter(target_dir, filename, title):
    """
    修改 md 文件中 Front-matter 里的 title 和 cover 字段的值
    Modify the value of the title and cover fields in the Front-matter of the md file

    其中，title 字段使用 title 值
    cover 字段为 yyyy/mm/filename/cover.jpg 路径，使用 date 字段中的年月来填充其值中的 yyyy/mm

    The title field uses the title value;
    The cover field is the yyyy/mm/filename/cover.jpg path,
    using the year and month in the date field to fill in the yyyy/mm in its value

    Args:
        target_dir: 目标文件夹路径 The target folder path
        filename: 文件名 The file name
        title: 文章标题 The title of the article
    """
    with open(target_dir / f'{filename}.md', 'r+', encoding='utf-8') as f:
        lines = f.readlines()
        front_matter_end_index = lines.index('---\n', 1) if '---\n' in lines[1:] else None

        if front_matter_end_index is None:
            raise ValueError("Invalid Front-matter format.")

        front_matter = ''.join(lines[:front_matter_end_index + 1])
        content = ''.join(lines[front_matter_end_index + 1:])

        # 解析 date 字段
        date_match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', front_matter)
        if not date_match:
            raise ValueError("Date field not found in Front-matter.")
        date_str = date_match.group(1)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        yyyy_mm = date_obj.strftime('%Y/%m')

        # 更新 title 和 cover 字段
        front_matter = re.sub(r'title:\s*.*', f'title: {title}', front_matter)
        front_matter = re.sub(r'cover:\s*.*', f'cover: {yyyy_mm}/{filename}/cover.jpg', front_matter)

        # 写入修改后的内容
        f.seek(0)
        f.write(front_matter)
        f.write(content)
        f.truncate()


def new_draft(title: str):
    """
    创建 Hexo 草稿
    Create a Hexo draft

    步骤如下：
    1. 获取与创建所需目录
    2. 调用 title2filename 函数，将标题转换为文件名
    3. 检测 _draft 目录下是否存在同名文件夹，如果存在则报错
    4. 调用 hexo_cmd 函数，使用 hexo new post 命令创建一个新文章
    5. 将新文章移动到 _draft 目录下的同名文件夹中
    6. 删除 source/_posts 下的源文件和同名文件夹
    7. 将 md 文件中 Front-matter 里的 title 字段的值修改为 title, 补全 cover 字段的路径

    Steps:
    1. Get and create the required directories
    2. Call the title2filename func to convert the title to a file name
    3. Check if there is a folder with the same name
       in the _draft directory, if so, report an error
    4. Call the hexo_cmd func to create new article using the hexo new post command
    5. Move the new article to the folder with the same name in the _draft dir
    6. Delete the source file and folder with the same name under source/_posts
    7. Modify the value of the title field in the Front-matter of the md file to title,
       and complete the path of the cover field

    Args:
        title: 草稿标题 The title of the draft
    """
    # 1. 获取与创建所需目录
    source_posts_dir, draft_dir, _, _ = check_get_make_dirs()

    # 2. 将标题转换为文件名
    filename = title2filename(title)
    target_dir = draft_dir / filename

    # 3. 检测 _draft 目录下是否存在同名文件夹
    if target_dir.exists():
        raise FileExistsError(red(f"Draft '{target_dir}' already exists."))

    # 4. 使用 hexo new post 命令创建一个新文章
    exec_hexo_cmds([f'new post "{filename}"'])
    # 查找新创建的文章路径
    post_md = next(source_posts_dir.glob(f'{filename}.md'), None)
    if not post_md:
        raise FileNotFoundError(red(f"Post file for '{filename}' not found."))

    # 5. 创建目标文件夹并移动文章
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(post_md), str(target_dir / f'{filename}.md'))

    # 6. 删除 source/_posts 下的同名文件夹（如果有）
    post_dir = source_posts_dir / filename
    if post_dir.exists():
        shutil.rmtree(post_dir)

    # 7. 修改 md 文件中 Front-matter 里的 title 和 cover 字段的值
    change_front_matter(target_dir, filename, title)

    print(f"Draft '{blue(title)}' has been created and moved to {green(target_dir)}.")


def new_drafts(titles: Union[list[str], str]):
    """
    创建多个 Hexo 草稿
    Create multiple Hexo drafts

    Args:
        titles: 草稿标题列表或字符串
                List of draft titles or a string of title
    """
    if isinstance(titles, str):
        titles = [titles]
    for title in titles:
        new_draft(title)


def avoid_process_code_blocks(
        content: str,
        process_func,
        avoid_inline_code=True,
) -> str:
    """
    对传入文章内容执行传入的函数，保证代码块中的内容不被处理
    Execute the incoming function on the incoming article content,
    ensuring that the content in the code block is not processed

    Args:
        content: 文章内容 The content of the article
        process_func: 处理函数 The processing function
        avoid_inline_code: 是否避免处理行内代码或代码块中的内容
            Whether to avoid processing the content in inline code or code blocks

    Returns:
        modified_content: 修改后的文章内容 The modified content of the article
    """
    # 定义用于提取代码块的正则表达式
    code_block_pattern = re.compile(r'(~~~[\s\S]*?~~~|```[\s\S]*?```|`[^`]*`)')
    if not avoid_inline_code:
        code_block_pattern = re.compile(r'(~~~[\s\S]*?~~~|```[\s\S]*?```)')

    # 分割文本为代码块和非代码块部分
    parts = []
    last_end = 0
    for match in code_block_pattern.finditer(content):
        start, end = match.span()
        # 处理非代码块部分
        if start > last_end:
            parts.append(process_func(content[last_end:start]))
        # 保留代码块部分不变
        parts.append(match.group())
        last_end = end
    # 处理最后一段非代码块（如果有的话）
    if last_end < len(content):
        parts.append(process_func(content[last_end:]))

    # 合并处理后的部分
    modified_content = ''.join(parts)
    return modified_content


def remove_img_path_in_md(content: str, img_dir: str = "img/") -> str:
    """
    使用正则表达式替换形如 [<...>](img/<...>) 和 <img src="img/<...>" 的语句，
    去掉其中的 `img/`，仅保留文件名。
    Use regular expressions to replace statements like [<...>](img/<...>) and <img src="img/<...>",
    remove `img/` and keep only the file name.

    另外，对于行内代码或代码块中的图片插入语句，不做处理。
    In addition, for image insertion statements 
    in inline code or code blocks, no processing is done.

    Args:
        content: 文章内容 The content of the article
        img_dir: 将要被删去的图片文件夹路径 The image folder path to be removed

    Returns:
        modified_content: 修改后的文章内容 The modified content of the article
    """

    def process_non_code(text):
        # 正则表达式模式：匹配 Markdown 图片链接和 HTML <img> 标签
        img_insert_pattern = rf'\[(.*?)\]\(({img_dir})?([^)]+)\)'
        html_img_tag_pattern = rf'<img\s+src=["\']{re.escape(img_dir)}([^"\']+)["\']'

        def replace_img_path(match):
            # 提取 match 中的组，去掉 img/
            return f'[{match.group(1)}]({match.group(3)})'

        def replace_html_img_src(match):
            # 仅保留文件名，移除 img/
            return f'<img src="{match.group(1)}"'

        # 替换 Markdown 图片链接中的 img/
        text = re.sub(img_insert_pattern, replace_img_path, text)
        # 替换 HTML <img> 标签中的 img/
        text = re.sub(html_img_tag_pattern, replace_html_img_src, text)
        return text

    modified_content = avoid_process_code_blocks(content, process_non_code)
    return modified_content


def remove_first_level_titles(content: str) -> str:
    """
    去掉文章内容中的一级标题（# 标题），移除一级标题语句两边的换行。
    Remove first-level titles (# Title) from the article content,
    and also remove surrounding newlines.

    另外，对于代码块中的一级标题，不做处理。
    In addition, for the first-level titles in  code blocks, no processing is done.

    Args:
        content: 文章内容 The content of the article

    Returns:
        modified_content: 修改后的文章内容 The modified content of the article
    """
    def process_non_code(text):
        # 去掉一级标题语句和两边的换行
        first_level_title_pattern = re.compile(r'\n^#\s+.+\n', re.MULTILINE)
        return first_level_title_pattern.sub('', text)

    modified_content = avoid_process_code_blocks(content, process_non_code, False)
    return modified_content


def replace_url_to_card(content: str) -> str:
    """
    将文章内容中的带有特定注释的 URL 替换为卡片链接
    Replace URLs with specific comments in the article content with card links

    特定内容如下：
    The specific content is as follows:
    ```
    <!-- <website-icon-url> -->
    [<website-title>](<website-url>)
    ```

    将会转换为：
    Will be converted to:
    ```
    {% externalLinkCard "<website-title>" "<website-url>" "<website-icon-url>" %}
    ```

    特别地，如果 <website-icon-url> 为如下固定值，将会被替换为相应网站的 logo URL：
    In particular, if <website-icon-url> is the following fixed value,
    it will be replaced with the logo URL of the corresponding website:
    - `知乎` / `zhihu`: `https://pic1.zhimg.com/v2-4cd83ae3d6ca76dabecf001244a62310.jpg?source=57bbeac9`
    - `github`: `https://github.githubassets.com/assets/apple-touch-icon-144x144-b882e354c005.png`
    - ...

    Args:
        content: 文章内容 The content of the article

    Returns:
        modified_content: 修改后的文章内容 The modified content of the article
    """
    # 定义网站图标URL的映射
    icon_url_mapping = {
        '知乎': 'https://pic1.zhimg.com/v2-4cd83ae3d6ca76dabecf001244a62310.jpg?source=57bbeac9',
        'zhihu': 'https://pic1.zhimg.com/v2-4cd83ae3d6ca76dabecf001244a62310.jpg?source=57bbeac9',
        'github': 'https://github.githubassets.com/assets/apple-touch-icon-144x144-b882e354c005.png'
    }

    # 正则表达式模式，用于匹配特定格式的注释和链接
    pattern = re.compile(
        r'<!--\s([^>]+?)\s-->\n\[(.*?)\]\((.*?)\)',
        re.DOTALL
    )

    def replace_with_card(match):
        icon_url = match.group(1).strip()
        title = match.group(2).strip()
        url = match.group(3).strip()

        # 如果 <website-icon-url> 是特定值，则替换为对应的 logo URL
        if icon_url.lower() in map(str.lower, icon_url_mapping.keys()):
            icon_url = icon_url_mapping[icon_url.lower()]

        return f'{{% externalLinkCard "{title}" "{url}" "{icon_url}" %}}'

    modified_content = pattern.sub(replace_with_card, content)
    return modified_content


def finalize_all_drafts():
    """
    将所有 _draft 文件夹下的草稿经修改后复制到 source/_posts 目录下
    Copy all drafts in the _draft folder to the source/_posts directory after modification

    _draft 文件夹下的文章结构为：
    The structure of the article in the _draft folder is as follows:

    _draft
    ├── article1
    │   ├── article1.md
    │   └── img
    │       ├── cover.jpg
    │       └── img1.jpg
    ├── article2
    │   ├── article2.md
    │   └── img
    │       ├── cover.jpg
    │       └── img1.jpg
    └── article3...

    复制之后 source/_posts 目录下的文章结构为：
    The structure of the article in the source/_posts
    directory after copying is as follows:

    source/_posts
    ├── article1.md
    ├── article2.md
    ├── article1
    │   ├── cover.jpg
    │   └── img1.jpg
    ├── article2
    │   ├── cover.jpg
    │   └── img1.jpg
    └── article3...

    文章中需要修改的内容为：
    1. 删除图片插入语句中的 "img/"
    2. 删除文章中的一级标题
    3. 将附带特殊注释的 URL 替换为卡片链接

    The content that needs to be modified in the article is:
    1. remove "img/" in the image insertion statement
    2. remove the first-level title in the article
    3. replace URLs with special comments with card links
    """
    # 获取所需目录
    source_posts_dir, draft_dir, _, _ = check_get_make_dirs()

    # 遍历 _draft 目录下的所有草稿文件夹
    for article_dir in draft_dir.iterdir():
        if not article_dir.is_dir():
            continue

        article_name = article_dir.name
        article_md = article_dir / f'{article_name}.md'
        img_src_dir = article_dir / 'img'

        if not article_md.exists():
            continue
        # 新的文章路径和图片目标路径
        post_md_dest = source_posts_dir / f'{article_name}.md'
        img_dest_dir = source_posts_dir / article_name
        print(f"Finalizing draft '{blue(article_name)}' "
              f"to {green(post_md_dest)}...")

        # 如果 source_posts_dir 中已有该文章及其同名文件夹，则删除
        if post_md_dest.exists():
            post_md_dest.unlink()
        if img_dest_dir.exists():
            shutil.rmtree(img_dest_dir)
        # 创建图片目标文件夹
        img_dest_dir.mkdir(parents=True, exist_ok=True)
        # 复制图片
        if img_src_dir.exists():
            for img in img_src_dir.iterdir():
                shutil.copy(img, img_dest_dir / img.name)

        # 读取文章内容并修改图片路径
        with open(article_md, 'r', encoding='utf-8') as file:
            content = file.read()
        # 使用正则表达式清理图片路径
        content = remove_img_path_in_md(content)
        # 删除一级标题
        content = remove_first_level_titles(content)
        # 将特殊注释的 URL 替换为卡片链接
        content = replace_url_to_card(content)
        # 写入修改后的内容到新的位置
        with open(post_md_dest, 'w', encoding='utf-8') as file:
            file.write(content)

        print(f"Draft '{blue(article_name)}' has been finalized"
              f" and copied to {green(post_md_dest)}.")


def refresh_hexo():
    """
    刷新 Hexo，相当于执行 hexo clean && hexo g
    Refresh Hexo, which is equivalent to executing hexo clean && hexo g
    """
    exec_hexo_cmds(['clean', 'g'])


def start_hexo_server():
    """
    启动 Hexo 服务器
    Start Hexo server

    如需在重新运行服务器后打开预览，应先执行 preview_hexo 函数，再执行本函数
    If you want to open the preview after restarting the server,
    you should execute the preview_hexo func first, then execute this func
    """
    # 检查 4000 端口是否被占用，若是则报错
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('localhost', 4000)) == 0:
            raise RuntimeError(f"Port 4000 is already in use.")
    # 执行 hexo s 命令，启动 Hexo 服务器
    exec_hexo_cmds('s')


def preview_hexo():
    """
    预览博客
    Preview the blog

    如需在重新运行服务器后打开预览，应先执行本函数，再执行 start_hexo_server 函数
    If you want to open the preview after restarting the server,
    you should execute this func first, then execute the start_hexo_server func
    """
    port = 4000
    # 使用默认浏览器打开 http://localhost:4000
    os.system(f'start http://localhost:{port}')


def refresh_preview_hexo():
    """
    刷新并预览 Hexo
    Refresh and preview Hexo
    """
    refresh_hexo()
    preview_hexo()
    start_hexo_server()


def deploy_hexo():
    """
    部署 Hexo
    Deploy Hexo
    """
    exec_hexo_cmds('d')


if __name__ == "__main__":
    """
    当没有附带任何参数运行时，为以后可能的 GUI 界面保留，目前展示帮助；
    当有参数时，提供命令行运行方式，支持以下命令：
    -n：调用 new_draft 函数，用于创建新的文章草稿并移动到 _draft 目录下；
    -f：调用 finalize_all_drafts 函数，用于将 _draft 目录下的文章调整后移入 source 文件夹；
    -r：调用 refresh_hexo 函数，用于重新生成静态文件；
    -s：调用 start_hexo_server 函数，用于启动 Hexo 服务器；
    -p：调用 preview_hexo 函数，用于打开预览网页；
    -rs：先调用 refresh_hexo 函数，再调用 start_hexo_server 函数；
    -sp 或 -ps：先调用 preview_hexo 函数，再调用 start_hexo_server 函数；
    -rps 或 -rsp：先调用 refresh_hexo 函数，再调用 preview_hexo 函数，最后调用 start_hexo_server 函数；
    -d：调用 deploy_hexo 函数，用于部署。
    """
    import argparse

    parser = argparse.ArgumentParser(description="Hexo Blog Management Tool")
    action_group = parser.add_mutually_exclusive_group()  # 添加互斥组，确保一次只运行一个主要操作

    action_group.add_argument(
        '-n', '--new', nargs='+',
        help='Create a new draft with the given title (hexo new post "<title>"), and move it to _draft'
    )
    action_group.add_argument(
        '-f', '--finalize', action='store_true', 
        help='Finalize all drafts, move them to source/_posts and modify the content'
    )
    action_group.add_argument(
        '-r', '--refresh', action='store_true', 
        help='Refresh Hexo (hexo clean && hexo generate)'
    )
    action_group.add_argument(
        '-s', '--start', action='store_true', help='Start Hexo server (hexo server)'
    )
    action_group.add_argument(
        '-p', '--preview', action='store_true', help='Preview the blog (start http://localhost:4000)'
    )
    action_group.add_argument(
        '-rs', '--refresh_start', action='store_true', 
        help='Refresh and start Hexo server (hexo clean && hexo generate && hexo server)'
    )
    action_group.add_argument(
        '-sp', '--start_preview', action='store_true', 
        help='Start server and preview the blog (start http://localhost:4000 && hexo server)'
    )
    action_group.add_argument(
        '-ps', '--preview_start', action='store_true', 
        help='Start server and preview the blog (start http://localhost:4000 && hexo server)'
    )
    action_group.add_argument(
        '-rps', '--refresh_preview_start', action='store_true', 
        help='Refresh, preview and start server (hexo clean && hexo g && start http://localhost:4000 && hexo s)'
    )
    action_group.add_argument(
        '-rsp', '--refresh_start_preview', action='store_true', 
        help='Refresh, preview and start server (hexo clean && hexo g && start http://localhost:4000 && hexo s)'
    )
    action_group.add_argument(
        '-d', '--deploy', action='store_true', help='Deploy the blog (hexo deploy)'
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 检查是否提供了任何参数
    if not any(vars(args).values()):
        # 如果没有提供任何参数，则显示帮助信息
        parser.print_help()
    else:
        # 根据提供的参数执行相应的函数
        if args.new:
            new_drafts(args.new)
        elif args.finalize:
            finalize_all_drafts()
        elif args.refresh:
            refresh_hexo()
        elif args.start:
            start_hexo_server()
        elif args.preview:
            preview_hexo()
        elif args.refresh_start:
            refresh_hexo()
            start_hexo_server()
        elif args.start_preview or args.preview_start:
            preview_hexo()
            start_hexo_server()
        elif args.refresh_preview_start or args.refresh_start_preview:
            refresh_hexo()
            preview_hexo()
            start_hexo_server()
        elif args.deploy:
            deploy_hexo()
