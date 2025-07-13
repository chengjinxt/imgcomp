# imgcomp
图片压缩

# 创建工程
使用PySide6创建界面程序

# 功能
1. 选择图片
2. 压缩图片
3. 保存图片
4. 显示图片信息

# 压缩图片通过调用命令行程序 imagecomp.exe
imagecomp.exe <input_file> -o <output_file> -q <quality>
imagecomp.exe ./images/test.jpg -o test.jpg -q 80
更多使用方法参考
imagecomp.exe --help
Usage: imagecomp.exe [OPTIONS] FP

  Compress images via command line.

  :param fp: Image file path or directory path. :type fp: str

  :param force: Whether to overwrite if a file with the same name exists,
  defaults to False. :type force: bool

  :param quality: Compression quality. 80-90, or 90, default is 80. :type
  quality: int or tuple[int, int]

  :param output: Output path or output directory. :type output: str

  :param webp: Convert images to WebP format, default is False. :type webp:
  bool

  :param target_size: Target file size in KB. When specified, quality is
  ignored. :type target_size: int or None

  :param size_range: Min and max size in KB. Tries to maintain quality while
  ensuring size is within range. :type size_range: tuple(int, int) or None

  :param webp_quality: Quality for WebP conversion (1-100). Default is 100.
  :type webp_quality: int

Options:
  -f, --force, --violent        Whether to overwrite if a file with the same
                                name exists, defaults to False.
  -q, --quality QUALITYINTEGER  Compression quality. 80-90, or 90, default is
                                80.
  -o, --output TEXT             Output path or output directory.
  --webp                        Convert images to WebP format, default is
                                False.
  -t, --target-size INTEGER     Target file size in KB. When specified,
                                quality is ignored.
  -s, --size-range INTEGER...   Min and max size in KB. Tries to maintain
                                quality while ensuring size is within range.
  -wq, --webp-quality INTEGER   Quality for WebP conversion (1-100). Default
                                is 100.
  --help                        Show this message and exit.

  # 要求
  请根据上面的命令行参数，合理设计界面布局，要美观，大方，合理。

# 安装和运行

## 环境要求
- Python 3.7+
- PySide6
- requests
查看PySide6版本号
输入以下命令并按回车执行：
E:/ProgramData/anaconda3/envs/py311_pyside6_env/python.exe -c "import PySide6; print(PySide6.__version__)"
6.7.2
这将输出 PySide6 的版本号。如果你需要查看用于编译 PySide6 的 Qt 版本，可以使用类似的命令：
E:/ProgramData/anaconda3/envs/py311_pyside6_env/python.exe  -c "from PySide6.QtCore import __version__; print(__version__)"
6.7.3

## 安装依赖
```bash
pip install -r requirements.txt
```

## 运行程序
### Windows
双击 `run.bat` 文件或在命令行中运行：
```bash
python main.py
```

### Linux/Mac
```bash
chmod +x run.sh
./run.sh
```

# 功能特性

## 界面布局
- **左侧控制面板**：文件选择、压缩设置、操作按钮、执行日志
- **右侧图片面板**：图片信息显示、原始图片预览、压缩后图片预览

## 主要功能
1. **广告走马灯**：在界面顶部显示广告信息，支持自动切换和手动切换
2. **文件选择**：支持选择输入图片文件和输出位置
3. **压缩设置**：
   - 质量优先模式：设置压缩质量（1-100）
   - 目标大小模式：指定目标文件大小（KB）
   - 大小范围模式：设置最小和最大文件大小
   - WebP转换：可选择转换为WebP格式
4. **图片预览**：显示原始图片和压缩后图片的对比
5. **信息显示**：显示文件名、大小、尺寸、格式等详细信息
6. **设置保存**：自动保存和加载用户设置
7. **广告交互**：点击广告文字可打开图片或网页链接

## 压缩模式说明
- **质量优先**：通过调整质量参数来控制压缩程度
- **目标大小**：指定目标文件大小，程序自动调整质量
- **大小范围**：在指定大小范围内保持最佳质量

## 支持的图片格式
- 输入：JPG, JPEG, PNG, BMP, GIF, WebP
- 输出：JPG, JPEG, PNG, BMP, GIF, WebP（可选择转换）

## 广告功能说明
- **数据来源**：从指定API获取广告数据
- **显示方式**：走马灯形式，每5秒自动切换
- **交互功能**：
  - 点击广告文字可打开对应链接
  - 图片链接：在客户端内打开图片查看器
  - 网页链接：调用系统默认浏览器打开
  - 支持手动切换广告（左右箭头按钮）
  - 可关闭广告横幅


# 在界面最上部分显示广告信息
广告信息通过下面方面获取
curl --location 'http://xxxx/record/fetch' \
--header 'Content-Type: application/json' \
--data '{
  "classId":1274,
  "syncTime":1519297787000
}'
获取返回的数据如下
{
    "code": 0,
    "msg": "SUCCESS",
    "data": {
        "dataList": [
            {
                "id": 10190,
                "classId": 1274,
                "sortNum": 0,
                "title": "B站",
                "label": "bilibili",
                "relativePath": "https://space.bilibili.com/1936309816",
                "fileSize": 0,
                "fileType": "",
                "contentHtml": "",
                "contentPlain": "",
                "status": 0,
                "modifyTime": 1752387913815,
                "createTime": 1752387913815
            },
            {
                "id": 10191,
                "classId": 1274,
                "sortNum": 0,
                "title": "视频号",
                "label": "",
                "relativePath": "http://www.firemail.wang:8088/chunhui_resource/upload/1752388351141.JPG",
                "fileSize": 92826,
                "fileType": "JPG",
                "contentHtml": "",
                "contentPlain": "90KB",
                "status": 0,
                "modifyTime": 1752388366720,
                "createTime": 1752388366720
            },
            {
                "id": 10192,
                "classId": 1274,
                "sortNum": 0,
                "title": "公众号",
                "label": "",
                "relativePath": "http://www.firemail.wang:8088/chunhui_resource/upload/1752388383451.JPG",
                "fileSize": 27769,
                "fileType": "JPG",
                "contentHtml": "",
                "contentPlain": "27KB",
                "status": 0,
                "modifyTime": 1752388386216,
                "createTime": 1752388386216
            },
            {
                "id": 10193,
                "classId": 1274,
                "sortNum": 0,
                "title": "加微信好友",
                "label": "",
                "relativePath": "http://www.firemail.wang:8088/chunhui_resource/upload/1752388459034.JPG",
                "fileSize": 86611,
                "fileType": "JPG",
                "contentHtml": "",
                "contentPlain": "84KB",
                "status": 0,
                "modifyTime": 1752388477754,
                "createTime": 1752388477754
            },
            {
                "id": 10194,
                "classId": 1274,
                "sortNum": 0,
                "title": "微信群聊",
                "label": "",
                "relativePath": "http://www.firemail.wang:8088/chunhui_resource/upload/1752388615731.PNG",
                "fileSize": 166831,
                "fileType": "PNG",
                "contentHtml": "",
                "contentPlain": "162KB",
                "status": 0,
                "modifyTime": 1752388617450,
                "createTime": 1752388617450
            }
        ],
        "lastModTime": 1752388617450
    }
}
提取dataList数组中的数据，每个元素取数据对象的title字段的值做为广告走马灯显示，当用户点击显示的文字时，取对象relativePath字段的值，如果relativePath的链接指向一个图片，则直接在客户端内打开一个显示图片的窗口，如果relativePath的链接指向一个网站，则调用系统默认浏览器打开此链接。


# 制作图标
图标编辑器（在线工具等）制作一个 256x256 的 .ico 文件，命名为 imgcomp.ico，放在你的项目根目录。
https://www.ailogoeasy.com/zh

# 打包
检查python环境
pip show PySide6
如果没有安装
则通过切换conda环境
conda env list
conda create --name py311_pyside6_env python=3.11.11
激活选中的环境
activate py311_pyside6_env

在命令行下要使用conda设置的环境

pyinstaller --noconfirm --windowed --onefile --name imgcomp --icon imgcomp.ico --add-binary "imagecomp.exe;." --add-data "imgcomp.ico;." --hidden-import PySide6.QtCore --hidden-import PySide6.QtGui --hidden-import PySide6.QtWidgets main.py

