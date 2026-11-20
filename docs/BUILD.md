# 从源码构建

源码仓库不跟踪工具链、静态库、DLL、编译成品或固件。最省事的开发入口是
Release 中的 Windows x64 ZIP；它包含已编译工具链及五个程序。

## Windows

安装 Python 3.10+、Git 和 MSYS2。在 MSYS2 UCRT64 终端安装：

```sh
pacman -S --needed mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-make
```

在能找到 Python、`gcc` 和 `mingw32-make` 的终端中执行（也可将 MSYS2 的
`ucrt64/bin` 加入当前 PowerShell 的 PATH）：

```sh
git clone https://github.com/HelloClyde/BBK7980-sdk.git
cd BBK7980-sdk
python -X utf8 tools/install_toolchain.py
python -X utf8 tools/ci.py
python -X utf8 emulator-support/build.py
python -X utf8 tools/package.py
python -X utf8 tools/verify_release.py dist
```

第一步下载并校验固定 cc65 源码，不使用会变化的 Windows snapshot。
`--archive PATH` 可使用同一源码 ZIP 的本地副本，仍强制检查哈希。
源码 URL、完整提交与 SHA-256 在 `tools/install_toolchain.py` 中固定，
安装结果的 `toolchain/cc65/provenance.json` 同时记录这些信息。

`tools/ci.py` 会从 C/汇编源码构建全部示例、执行宿主 C 测试、检查五个
BJBBK.110 文件、逐一比对已完成模拟器验证的二进制哈希，并构建外部项目模板。
`tools/package.py` 只在 Windows 生成 win64 发行包。

普通应用编译不需要宿主 GCC，使用发布 ZIP 后可直接运行：

```sh
python -X utf8 tools/build.py examples/hello
python -X utf8 tools/new_project.py ../myapp --name 我的应用
python -X utf8 tools/build.py ../myapp
```

也可通过 `CC65_HOME` 或 `tools/build.py --compiler PATH` 指定工具链。
其他 cc65 版本可能改变二进制；1.1.0 的精确基线检查仍要求固定版本的结果。

## Linux

源码编译入口支持 PATH 中的 `gcc`、GNU `make` 和 Python 3.10+，构建器会选用
无 `.exe` 后缀的 cc65。公共发布流水线在 Windows 上运行，Linux 兼容性尚未
在本项目实际运行验证；Windows GUI/声音模块不适用于 Linux。

## 发行与复现范围

CI 的编译器来自上述固定源码；GCC/MSYS2/Python 使用 runner 及工作流声明的版本。
五个设备程序必须与已有模拟器验证结果逐字节相同。Windows 工具链自身和整个 ZIP
可能随宿主编译器变化；不承诺整个归档跨不同宿主工具版本逐字节相同。

ZIP 内部清单覆盖每个文件；Release 旁的 `SHA256SUMS.txt` 校验 ZIP 和构建报告。
发布 job 下载同一次成功构建的 artifact，校验后上传，不再次构建。
标签须与 `SDK.json` 一致；工作流不覆盖已发布的同名 Release。
