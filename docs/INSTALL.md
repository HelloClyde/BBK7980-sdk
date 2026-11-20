# 运行与真机安装

预编译程序位于发布包 `bin/`；源码构建结果位于示例的 `build/`。

## 真机（待首次实测）

本 SDK 按朗文 7980 V1.10 适配。先确认系统版本，备份个人资料，保证电量
及应用空间充足。真机尚未验证，先试运行 `开发演示.exe`，确认显示、方向键、
Esc 和 Home 都正常后再试扫雷。

1. 准备 7980 的专用串口下载线和对应的 PCLINK 1.10。
2. 连接电脑 COM 口及机器通讯口；使用 USB 转 RS-232 时先装驱动并确认 COM 号。
3. 电脑打开 PCLINK 选择对应串口。
4. 7980 进入“文件 → 电脑联机”，按 Enter。
5. 在 PCLINK 的文件下载功能中选择本包的应用 `.exe`，传输完成后退出联机。
6. 在“娱乐”栏目找到应用名，按 Enter 启动。

这是单个应用的文件传输，无需系统升级。SDK 不包含 PCLINK 安装程序，也没有
验证 PCLINK 是否接受这些新封装文件；出现兼容性提示应记录原样报错，继续
修正封装。原厂接线及电脑联机路径出自官网升级工具随附的准备说明。

## 模拟器

需要用户已有模拟器中的 V1.10 固件和 NAND 模板。下文的 `../bbk7980-emulator`
是示例路径，应替换为自己的模拟器目录；也支持 0.4 便携版的 BBK7980 文件夹
（自动识别 `_internal`）。源码检出先执行 `python emulator-support/build.py`
编译后端；发布 ZIP 已附该 DLL。
界面另需 Pillow；PSG 后端和 UART 工具已随 SDK 提供。

一次安装三个示例并直接打开新版扫雷：

```powershell
python -X utf8 tools/run_emulator.py --emulator ../bbk7980-emulator --minesweeper
```

此命令使用 SDK 下的 `build/emulator-session/` 存放 NAND 和会话数据。
文件和旋律演示：

```powershell
python -X utf8 tools/run_emulator.py --emulator ../bbk7980-emulator --example storage
python -X utf8 tools/run_emulator.py --emulator ../bbk7980-emulator --example music
```

运行工具使用随包的 PSG 后端和现有模拟器提供的固件，在 build 目录建立副本。
音乐窗口按 Enter/空格播放、Esc/Home 停止退出；存储窗口自动写入 SDKTEST.DAT，
F1 验证更新/覆盖/删除等操作。声音由 PSG 模型输出，电脑需有可用音频设备。
也可自行指定安装输入输出：

```powershell
python -X utf8 tools/emulator.py --emulator ../bbk7980-emulator `
  --source ../bbk7980-emulator/runtime/installed-nand.bin.z `
  --output build/my-apps.bin.z examples/minesweeper/build/扫雷.exe
python ../bbk7980-emulator/app.py --nand build/my-apps.bin.z --minesweeper
```

安装器读取并校验 PC 传输头，正常按键进入原厂电脑联机，再上传应用并下载读回。
`--source` 不改写，`--output` 必须是其他路径的 `.z` 压缩 NAND。

上例将扫雷作为娱乐第七项。自定义模板的栏目/条目排列可能不同，应从原厂菜单
手工选择。SDK 发布包不包含 ROM、完整 NAND 或系统字体。
