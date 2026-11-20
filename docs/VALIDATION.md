# 验证方法和边界

`validation/report.json` 是来宾端验证报告；截图直接来自原厂固件执行后的显存。
宿主只读取游戏 RAM 选择测试动作，不写棋盘、CPU 状态或中断使能。

验证从原厂预装 NAND 模板开始，用真实矩阵按键进入电脑联机，经过原厂串口
文件服务安装三个例子并读回，确认逐字节相同；再从娱乐目录正常加载执行。
1.1 另安装存储、音乐两个例子，19 项新检查验证原厂文件写入、关闭、NAND
导出/导入及 CPU 重启后的原厂 UART 读回，以及更新、覆盖、定位和删除。

旋律不是宿主预先播放的音频文件：来宾 C 代码实际写 PSG 寄存器，器件模型按
这些寄存器生成 PCM；报告记录非静音输出、首音约 262 Hz、完整结束及 Esc/Home
中止后的静音。`music-preview.wav` 是这段器件输出的录音。

覆盖 30 项断言：初始化 DATA 与 BSS、C 运算与中断共存、三种字号字节对照、
ROM 字符串文件查找、32 位文件长度、跨 NAND 页读取、EOF/错误 ID、系统周期
事件和按键、应用期间 CPU I 标志、扫雷胜负/重开、Esc/Home 退出、重复启动。

中断检查不是只在程序退出时查看状态：主动触发扫雷绘制，逐指令观察应用
程序区的指令，排除内核中断现场；观测范围内应用的 I 标志必须始终为 0，
同时原厂 IRQ 服务计数增加。原厂内核自己进入短临界区不算应用关闭中断。

宿主 C 测试补充非对齐矩形、右下越界、空区域、两位像素顺序、图块裁剪；
扫雷规则验证首击邻域安全、洪泛边界、插旗保护、胜负与连开。

公共 CI 执行 `python tools/ci.py`，不依赖固件。以下是另行复跑模拟器的步骤，
需 Pillow、GCC 及用户自行提供的模拟器运行资产（固件、NAND、兼容字体）；
固件审计另需 pefile。源码检出先运行 `python emulator-support/build.py`。

```powershell
python -X utf8 tools/build.py examples/hello
python -X utf8 tools/build.py examples/diagnostics
python -X utf8 tools/build.py examples/minesweeper
python -X utf8 tools/build.py examples/storage
python -X utf8 tools/build.py examples/music
python -X utf8 -m unittest discover -s tests -v
python -X utf8 tests/validate_native.py --emulator ../bbk7980-emulator
python -X utf8 tests/validate_io.py --emulator ../bbk7980-emulator
```

另从发行 ZIP 解压出的副本重新构建，校验例子有效载荷一致，以验证工具链和
SDK 可脱离本工作区使用。发行文件 SHA256 记录在 `SHA256SUMS.txt`。

未完成：真机运行、PCLINK 实际传输接受、硬件总线/电源、语音及压缩音频解码、RTC、V1.00。
这些限制不会因模拟器检查通过而被视为已完成。
