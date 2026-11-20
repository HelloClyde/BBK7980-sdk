# 本地验证证据

这些是 1.1.0 在执行原厂固件的模拟器中的已有本地记录，公共 CI 不下载固件。
`report.json` 的 30 项和 `io-report.json` 的 19 项检查包含来宾运行与 UART 读回；
其中安装记录的哈希针对 **32 KiB 设备有效载荷**。
`relocation.json` 记录五个 **32,896 字节 PC 传输文件** 的完整 SHA-256。
CI 同时核对这两种哈希，防止把编译通过当作任意新二进制已验证。

`host-tests.json`、`board-regression.json` 是此前本地宿主测试的摘要。
各 PNG 为 SDK 示例实际显存截图；`music-preview.wav` 是 PSG 模型生成 PCM 的录音。
运行时提供的字体是兼容输入，未确认等同 7980 原厂字形；仓库及发布包不带该字体。

新的 CI 构建报告由构建器生成，随 Release 的 `build-report.json` 分发，
也放在发行 ZIP 的 `validation/ci-report.json`。它明确区分 CI 检查和既有模拟器证据。

真机运行、PCLINK 传输、模拟器未建模的硬件特性，以及通用音频解码均未由这些报告证明。
