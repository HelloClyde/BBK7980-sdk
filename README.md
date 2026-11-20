# BBK7980 SDK 1.1.0

[![Build](https://github.com/HelloClyde/BBK7980-sdk/actions/workflows/build-release.yml/badge.svg)](https://github.com/HelloClyde/BBK7980-sdk/actions/workflows/build-release.yml)

面向朗文 7980 **V1.10** 的社区 C/65C02 原生应用 SDK。根据官网升级包中的
原厂游戏和系统程序分析调用约定，提供独立头文件、静态库、启动代码、构建和
打包工具、项目模板及五个可运行示例。本项目由社区整理维护。

应用通过原厂事件系统接收按键，等待时进入原厂事件泵，正常服务系统中断。
cc65 与原厂调用约定由运行库切换；应用代码没有 SEI，也不改写中断使能寄存器。
原厂内核自身的短临界区保持原有行为。

## 快速开始

从 [v1.1.0 Release](https://github.com/HelloClyde/BBK7980-sdk/releases/tag/v1.1.0)
下载 `BBK7980-SDK-1.1.0-win64.zip` 和 `SHA256SUMS.txt`。这是社区预发布，
适配 7980 V1.10，已完成原厂固件模拟器验证，真机与 PCLINK 待实测。

Windows x64 发布包已附固定版本 cc65。另需 Python 3.10 或更新版本；普通构建
只使用 Python 标准库，不需要 Pillow、GCC、pefile 或模拟器。

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
python -X utf8 tools/build.py examples/hello
python -X utf8 tools/ci.py
```

工具链从固定 cc65 提交的源码 ZIP 构建，先校验 SHA-256；仓库没有 SDK 子模块。
发布 ZIP 则附带已构建的 Windows 工具链，日常开发只需 Python。

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
| 应用图标、娱乐条目、封装校验 | 原厂 BJBBK.110 容器及每 16 KiB 区校验 |
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

公共 CI 从源码构建工具链和五个示例、执行 13 项宿主 C 测试、校验封装与
模拟器已验证二进制的 SHA-256，并检查项目模板。它不下载原厂固件，也不声称
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
| 发布 ZIP 开发 | Windows x64、Python 3.10+；ZIP 含固定 cc65，无额外 Python 包 |
| 源码构建 / 宿主测试 | Python 3.10+、GCC、GNU make；cc65 固定提交见下方 |
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
