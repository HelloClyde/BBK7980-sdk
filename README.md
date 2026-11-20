# BBK7980 SDK 1.1.1

[![Build](https://github.com/HelloClyde/BBK7980-sdk/actions/workflows/build-release.yml/badge.svg)](https://github.com/HelloClyde/BBK7980-sdk/actions/workflows/build-release.yml)

面向朗文 7980 **V1.10** 的社区 C/65C02 原生应用 SDK。根据官网升级包中的
原厂游戏和系统程序分析调用约定，提供独立头文件、静态库、启动代码、构建和
打包工具、项目模板及五个可运行示例。本项目由社区整理维护。

应用通过原厂事件系统接收按键，等待时进入原厂事件泵，正常服务系统中断。
cc65 与原厂调用约定由运行库切换；应用代码没有 SEI，也不改写中断使能寄存器。
原厂内核自身的短临界区保持原有行为。

## 快速开始

从 [v1.1.1 Release](https://github.com/HelloClyde/BBK7980-sdk/releases/tag/v1.1.1)
下载 `BBK7980-SDK-1.1.1-win64.zip` 和 `SHA256SUMS.txt`。这是社区预发布，
适配 7980 V1.10，已完成原厂固件模拟器验证，真机与 PCLINK 待实测。

Windows x64 发布包已附固定版本 cc65，另需 Python 3.10 或更新版本。
默认图标或原始 `.bin` 图标的普通构建只使用 Python 标准库，不需要 GCC、pefile
或模拟器；使用 PNG 图标或生成图标预览时另装 Pillow，见下方图标说明。

在 SDK 解压目录中运行：

```powershell
python -X utf8 tools/build.py examples/hello
python -X utf8 tools/build.py examples/minesweeper
```

成品为 `examples/hello/build/开发演示.exe` 和
`examples/minesweeper/build/扫雷.exe`。这是给 7980 的 BJBBK.110 文件，
由电脑端 PCLINK 选择并传送；安装见 [真机步骤](docs/INSTALL.md)。
发布包另在 `bin/` 提供五个预编译程序，包括存储和音乐演示。

新建自己的应用（输出目录必须不存在）：

```powershell
python -X utf8 tools/new_project.py ../myapp --name 我的应用
python -X utf8 tools/build.py ../myapp
```

也可双击 `build-examples.cmd` 构建全部示例。

使用成品：在电脑 PCLINK 中选择 `bin/开发演示.exe`，机器进入“文件 → 电脑联机”
接收后，从“娱乐”启动。应用由原厂文件服务管理，不需要复制到指定盘符或系统目录。
扫雷用方向键移动、Enter 翻开、空格插旗、N 重开；音乐演示 Enter/空格播放，
Esc/Home 返回。完整接线与安装步骤见 [INSTALL](docs/INSTALL.md)。

从 GitHub 源码构建（先安装 Python、GCC、GNU make；Windows 见 [BUILD](docs/BUILD.md)）：

```powershell
git clone https://github.com/HelloClyde/BBK7980-sdk.git
cd BBK7980-sdk
python -X utf8 tools/install_toolchain.py
python -m pip install -r requirements-images.txt
python -X utf8 tools/build.py examples/hello
python -X utf8 tools/ci.py
```

工具链从固定 cc65 提交的源码 ZIP 构建，先校验 SHA-256；仓库没有 SDK 子模块。
发布 ZIP 则附带已构建的 Windows 工具链；PNG 图标依赖是可选安装项。

## 应用名称、图标与分类

这些属性在应用目录的 `project.json` 中配置，构建器已支持自定义图标和原厂分类。
例如，项目目录中放置 `main.c` 和 `icon.png`，配置为：

```json
{
  "name": "我的应用",
  "category": 9,
  "sources": ["main.c"],
  "icon": "icon.png"
}
```

`name` 是桌面名称及输出文件名，最多 **8 个 GBK 字节**（例如 4 个常用汉字）；
构建上述项目将生成 `build/我的应用.exe`。

### 自定义图标

**从 1.1.1 起支持直接使用 PNG，也提供独立转换脚本。**
`icon` 是相对于应用目录的文件路径，可写成 `icon.png`、`assets/icon.png` 或原始 `icon.bin`；
省略时使用 SDK 默认图标。

先安装 PNG/预览所需的 Pillow（不随 SDK 捆绑）：

```powershell
python -m pip install -r requirements-images.txt
```

把 PNG 放进项目，按上面的 JSON 配置后正常构建即可，无需先生成 `.bin`：

```powershell
python -X utf8 tools/build.py ../myapp
```

PNG 可使用任意尺寸，支持 RGB、RGBA、灰度和带透明色的索引图。转换时将透明像素与
白色背景合成，按亮度转为四级灰度；保持宽高比缩放到 **32×24** 内并居中，
空白处填最浅色，不裁切图片，默认无抖动。建议按 32×24 设计；正方形 PNG 会留左右空白。

也可以单独转换并查看量化后的可见区域：

```powershell
python -X utf8 tools/convert_icon.py ../myapp/icon.png -o ../myapp/icon.bin --preview ../myapp/icon-preview.png
```

输出 `icon.bin` 为 256 字节，预览为 32×24 PNG；省略 `-o` 时使用输入文件的同名 `.bin`。
如改用转换结果，在 `project.json` 中设置 `"icon": "icon.bin"`，之后构建就不再需要 Pillow。

原始 `.bin` 格式保持兼容：

- **256 字节的原始 2bpp 点阵**，按 32×32 像素存储，逐行排列，每行 8 字节。
- 每字节从高到低保存 4 个像素（位 7–6、5–4、3–2、1–0）；灰度值 0 最浅、3 最深。
  例如像素 `0, 1, 2, 3` 打包为 `0x1B`，不含图片文件头或调色板。
- **V1.10 原厂桌面显示顶部 32×24 像素**，底部 8 行不可见。
  PNG 转换器会自动将完整图片放进可见区域，再把底部 8 行填零；手工制作 `.bin` 时也应注意此限制。

可直接参考 [扫雷的配置](examples/minesweeper/project.json) 和
[自定义图标文件](examples/minesweeper/icon.bin)，或查看同一图标的
[PNG 示例](examples/minesweeper/icon.png)。

### 原厂分类

`category` 为 **1–11 的整数**，省略时默认为 **9（娱乐）**；项目模板也默认写入 9。
该值写入 BJBBK.110 传输头，安装工具据此将应用登记到对应栏目。
V1.10 的分类编号与名称如下，已与原厂升级包属性和运行中的原厂菜单交叉核对：

| category | 栏目 |
| --- | --- |
| 1 | 词典 |
| 2 | 背诵 |
| 3 | 课堂 |
| 4 | 听力 |
| 5 | 语法 |
| 6 | 阅读 |
| 7 | 作文 |
| 8 | 计算 |
| 9 | 娱乐 |
| 10 | 工具 |
| 11 | 文件 |

例如改为 `"category": 8`，重新构建并安装后应在“计算”栏目查找应用。
支持的是以上原厂固定栏目，不能通过这个字段新建或重命名分类；条目排序目前没有配置项。
已在原厂固件模拟器中将独立示例安装到 **4（听力）**，确认自定义图标的可见区域逐像素一致，
并从该栏目正常启动、响应按键及退出；真机/PCLINK 仍待实测。

修改名称、图标或分类后，都需要重新构建并传输新的应用 `.exe`。
SDK 自带五个示例均属于“娱乐”；自动演示和验证脚本按这一布局定位，
自定义分类的项目请从对应原厂菜单手动启动。

## 截图

以下为 SDK 示例在执行原厂 V1.10 固件的模拟器中的真实画面；
中文调用测试环境提供的字模服务，尚未核实字形与 7980 原机字库一致。

| 开发演示 | 扫雷 |
| --- | --- |
| ![开发演示](validation/hello.png) | ![扫雷进行中](validation/minesweeper-playing.png) |
| 文件写入 | PSG 音乐 |
| ![存储演示](validation/storage-written.png) | ![音乐演示](validation/music-playing.png) |

[试听模拟器 PSG 输出录音](validation/music-preview.wav)。此 WAV 是录音结果，
设备示例播放的是音符序列，没有实现 WAV/MP3 文件解码。

## 已实现接口

| 能力 | 实现方式 |
| --- | --- |
| 启动、C DATA/BSS、软件栈、退出 | 原厂初始化、堆分配/释放 + cc65 CRT |
| 按键、周期事件、系统快捷键 | 原厂事件泵及键码转换函数 |
| 12/16/24 点 GBK 字模与中文绘制 | 原厂字模文件服务，使用机器自己的字库 |
| 文件查找、读取、创建、更新、定位、关闭、删除 | 原厂文件服务；支持 EOF 截断及 ROM 常量写入 |
| 音符旋律与音量、Esc/Home 停止 | 复用原厂 PSG 寄存器配置；SDK 排序音符，中断保持运行 |
| 240×120 四灰阶绘图 | 显存点、线、裁剪矩形、单色图、12×12 图块 |
| 自定义图标、原厂分类、封装校验 | 原厂 BJBBK.110 容器及每 16 KiB 区校验 |
| 模拟器安装与验证 | 原厂电脑联机协议上传、读回；没有替换来宾函数 |

完整参数与约束见 [API](docs/API.md)，内存和调用依据见 [ABI](docs/ABI.md)。
当前单应用为一个 16 KiB 程序区，另一个 16 KiB 区存桌面数据；32 KiB 有效载荷，
128 字节电脑传输头，成品共 32,896 字节。

1.1 已加入文件写入/删除和 PSG 旋律。通用 WAV/MP3 解码、语音引擎、RTC、
应用动态内存及多程序区应用尚未列入公共 API。
没有确认的地址或占位接口不会作为已支持能力提供。`unsigned int` 在目标上是
16 位，事件结构为 3 字节；SDK 调用仅限主线程，不能从中断处理器重入。

## 示例与验证

- `hello`：原厂中文字体、四灰阶、方向键移动、Esc 返回。
- `diagnostics`：初始化数据、C 运算、中断共存、三种字号、文件查找/跨页读取/EOF。
- `minesweeper`：12×8、15 雷；原厂键盘事件驱动，运行时系统中断保持开启。
- `storage`：创建并写入 600 字节；F1 验证更新、定位、覆盖、只读保护和删除。
- `music`：Enter/空格播放约 4.5 秒的音阶旋律；Esc/Home 停止并退出。

已有验证：30 项基础来宾检查、19 项文件写入与旋律检查，包括持久化、原厂串口
读回、音频频率测量及系统 IRQ 持续服务；另有图形边界与游戏规则的宿主 C 检查。
具体结果、哈希、旋律 WAV 和截图随包
保存在 `validation/`。验证方法见 [验证记录](docs/VALIDATION.md)。

公共 CI 从源码构建工具链和五个示例，执行 13 项宿主 C 测试及 10 项图标转换测试、
校验封装与模拟器已验证二进制的 SHA-256，并检查项目模板和 PNG 图标入包。
它不下载原厂固件，也不声称
在 CI 中重新执行模拟器或真机测试。

**当前验证环境是执行原厂固件的模拟器，真机与 PCLINK 对本程序包的接受情况
尚待实测。正式版本号表示这组工具和 API 的发行版本，不表示完成了真机认证。**
本版本绑定的系统固件 SHA256：
`1f020acdb26a3081839e89f89f325649c231b89e7541505f9fa01edc4d4533a1`。
V1.00 或其他固件没有兼容承诺。

SDK 不附带原厂 ROM、字库或 PCLINK。字体由运行中的机器/模拟器提供。
新编写的 SDK 核心及工具采用 MIT；扫雷示例为 GPLv3，cc65 保留其原许可证，
详情见 [第三方说明](THIRD_PARTY.md)。可选的 `emulator-support/` 为 GPLv3，
包含更新的 PSG 模型、Windows 声音输出及对应源码。演示工具从现有模拟器读取
固件，在 SDK 的 build 目录创建运行副本，不覆盖现有模拟器文件。

## 依赖

| 用途 | 依赖 |
| --- | --- |
| 真机运行 | 朗文 7980 V1.10、机器已有字库；传输需专用下载线与 PCLINK 1.10，接受情况待实测 |
| 发布 ZIP 开发 | Windows x64、Python 3.10+；ZIP 含固定 cc65，默认/原始 `.bin` 图标无需额外 Python 包 |
| PNG 图标 / 图标预览 | 可选 Pillow 12.3.0：`python -m pip install -r requirements-images.txt` |
| 源码构建 / 宿主测试 | Python 3.10+、GCC、GNU make；完整测试另需上述 Pillow；cc65 固定提交见下方 |
| 可选模拟器 | Windows x64、Pillow、用户自行提供的固件及 NAND/font 输入；源码检出先编译 GPL 后端 |
| 可选固件审计 | pefile；输入为用户已有的原厂升级程序 |

cc65 V2.19 固定提交：
[`eebf54af545f4ae52f8489a2f6d4d5f93e7942d2`](https://github.com/cc65/cc65/tree/eebf54af545f4ae52f8489a2f6d4d5f93e7942d2)。
图标和图块是示例源码资产；不依赖额外字体生成工具。

## 感谢

感谢 [cc65](https://github.com/cc65/cc65) 的编译器和运行库；
[BBK 9288 GAM4980 Player](https://github.com/HelloClyde/BBK9288-gam4980)
及其上游 [无云 / BBK-simulator](https://gitee.com/BA4988/BBK-simulator/tree/BA4988/BA4988)、
[iyzsong / gam4980](https://codeberg.org/iyzsong/gam4980) 提供可选模拟器的 CPU 实现基础；[MAME](https://github.com/mamedev/mame)
的 ST2xxx 寄存器实现为独立板级模型提供交叉参考。
步步高官网历史升级资料用于核对原厂 ABI。各自许可与来源见 [THIRD_PARTY](THIRD_PARTY.md)，
原厂程序及字库版权保持原样。
