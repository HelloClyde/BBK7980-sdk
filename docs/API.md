# 1.1 API

包含 `bbk7980.h`，入口为 `int main(void)`，返回 0 退出到原厂调用者。
`bbk_u8/u16/u32` 在目标上分别占 1/2/4 字节。

## 事件和输入

`bbk_u8 bbk_event_wait(bbk_event *event)`：等待一个可交给应用处理的原厂事件。
`event` 必须是 RAM 中可写的 3 字节对象。非零表示收到事件。等待期间原厂
键盘扫描、周期事件和其他系统中断继续运行。原厂内核可能先处理 Home、
电源等系统快捷键，应用不一定收到对应原始键值。

`bbk_event`：`type` 为一字节，`value` 为两字节，按小端排列。
`BBK_EVENT_KEY=1` 的 `value` 是原始键号；`BBK_EVENT_PERIODIC=11` 为原厂
周期通知。未识别的类型应忽略。本 SDK 不把模拟器中的通知间隔定义为真机时间单位。

原始键：方向键 57/59/51/58（上/下/左/右），Enter 50，Esc 49，空格 34，
F1/F2 为 44/45，N 为 40。完整矩阵编号按行×8+列。

`bbk_event_translate(event)` 调用原厂键码转换，会就地修改事件的 `type` 和 `value`，
得到原厂事件类型与逻辑键码。普通文字为 `BBK_EVENT_TEXT=2`，功能键为
`BBK_EVENT_COMMAND=5`；已验证 Enter→类型5/值0x27、右→5/0x23、空格→2/0x20、
N→2/0x6e。返回值保留原厂结果。转换后的码表不能再与原始键常量混用。
`bbk_keys_flush()` 清空原厂待处理按键队列。

`bbk_u32 bbk_ticks(void)` 返回原厂中断递增的 32 位计数，起点未定义；用
无符号差值计算相对变化。高位重读取得一致快照，无需关闭中断。未确认真机
时钟频率，接口不承诺毫秒/秒单位。

## 字体

`bbk_u8 bbk_font_glyph(code,size,output)`：读取一个 GBK 双字节字模。
`size` 为 12/16/24；调用者分别提供 24/32/72 字节 RAM。每行高位像素在前，
12 点字每行两字节、低四位填充。非零表示已调用可用的原厂字库服务；0 表示
参数无效或系统未找到字库。未覆盖的合法字符可能得到空白或替代字模。

`bbk_text_gbk(x,y,text,size,shade)`：绘制 NUL 结束的 GBK 双字节字符串；返回
已绘制字数，遇到无效字节、ASCII 或屏幕边界停止。本接口不支持 UTF-8；可在
C 源码中使用 `\xD6\xD0` 这样的 GBK 字节转义。字符串可位于应用程序区，
字模缓冲由运行库在 RAM 中管理。绘字透明，不清除字模背景。

字库服务依赖机器原有 `font.bin`。SDK 不生成或安装替代字库。

## 文件

`bbk_u8 bbk_file_find(gbk_filename)`：由 NUL 结束的 GBK 文件名查找原厂文件 ID，
未找到返回 `BBK_FILE_INVALID=255`。名字含结束符最多 64 字节，空名字、空指针
或过长名字也返回 255。常量字符串会先复制到 RAM，再切换到系统程序区。

`bbk_u32 bbk_file_size(id)`：返回文件大小；255 返回 `0xffffffff`。
ID 只能使用本次运行中 `bbk_file_find` 成功取得的值，不应构造或保留跨启动 ID。

`bbk_u16 bbk_file_read_at(id,offset,output,length)`：按 32 位偏移读取，返回实际
字节数；到达 EOF 返回 0，越过末尾的请求截断；原厂错误或无效参数返回
`BBK_READ_ERROR=65535`。单次长度不超过 32767。输出必须是足够大的 RAM 缓冲，
不能跨越其内存区域。该接口不创建、覆盖或删除文件。

`bbk_u8 bbk_file_open(filename,mode)`：返回 0–3 的原厂流句柄，失败返回 255。
流句柄和 `bbk_file_find` 的目录 ID 是两种对象，不能混用。最多同时打开四个流。

| mode | 行为 |
| --- | --- |
| BBK_OPEN_READ | 以只读方式打开已有文件 |
| BBK_OPEN_REPLACE | 删除已有同名文件并新建，或直接新建；文件从零长度开始 |
| BBK_OPEN_UPDATE | 打开已有文件，定位写入时保留其他字节 |
| BBK_OPEN_CREATE | 仅新建；存在同名文件时报错 |

新数据文件使用与原厂串口下载相同的八个零元数据字节。REPLACE 通过原厂删除
和新建两个操作实现，没有断电原子性保证；新建失败时旧文件可能已经删除。

`bbk_u16 bbk_file_write(handle,data,length)`：返回写入长度，失败为
`BBK_IO_ERROR=65535`。最多 32767 字节；数据可在 RAM 或应用 ROM，运行库
分块复制到 RAM 后调用原厂写入函数。失败前可能已有部分数据写入。

`bbk_file_close(handle)`：提交原厂流并关闭，返回 0 成功、非零错误。写入后
必须关闭。正常返回 main 前关闭自己打开的流；不要依靠断电或 Home 中止来保存。

`bbk_file_seek(handle,offset,origin)`：返回 0 成功。origin=0 为绝对偏移，
origin=1 为向前移动 offset，origin=2 为从 EOF 向前回退 offset；因此 EOF/0
用于追加。offset 是非负数，超出原厂许可范围会失败。

`bbk_file_delete(filename)`：原厂删除操作，返回 0 成功。
`bbk_file_error()`：最近文件操作的错误值；6 为访问拒绝，7 为无效流句柄，
255 为 SDK 参数错误，其他值保留原厂含义。更新后重新查找目录 ID。

例如：

```c
bbk_u8 h=bbk_file_open("score.dat",BBK_OPEN_REPLACE);
if(h!=255) {
    bbk_file_write(h,"12345",5); /* ROM 常量也可直接写 */
    bbk_file_close(h);
}
```

## PSG 音符旋律

`bbk_u8 bbk_music_play(score,count,volume)`：播放 `bbk_note {hz,ticks}` 数组，
数组可位于 ROM 或 RAM；volume 为 0–15。hz=0 为休止，其余为 245–12000 Hz，
ticks 必须非零。返回 0 表示完整播放，49/52 表示 Esc/Home 取消，255 表示参数无效。
音高按 4 MHz CPU、PSGCK=2 MHz 的目标计算；真机时钟偏差尚需测量。

该调用阻塞调用者，等待时执行原机支持的 WAI。系统中断、键盘扫描及原厂计数
继续工作；从原厂按键队列读取 Esc/Home 停止，其他按键忽略。调用结束关闭
双通道 PSG。ticks 使用原厂中断计数，不承诺固定毫秒单位。

复用的是原厂提示音的 PSG 配置及硬件通道，音符排序是 SDK 新实现；没有把
单一提示音接口宣称为已恢复的通用音乐文件播放器。WAV/MP3 和语音解码不在此 API 中。

## 绘图

颜色 0/1/2/3 分别对应四级灰度。`bbk_pixel(x,y,shade)`、
`bbk_fill(x,y,width,height,shade)`、`bbk_hline`、`bbk_vline` 会裁剪到 240×120，
颜色取低两位。矩形允许任意像素对齐，边缘不会覆盖邻格像素。

`bbk_mono`：一位单色透明图，行宽为 `(width+7)/8` 字节，高位像素在前。
`bbk_glyph12`：连续的 12 点字模，每字 24 字节。
`bbk_tile12`：12×12 两位图块，每行 3 字节，高位像素在前；`selected` 非零
叠加光标角标。支持非对齐与边界裁剪，对齐的完整图块使用快速路径。

绘图直接更新原厂 2bpp 显存，允许系统中断运行，可能出现扫描过程中的轻微撕裂。
没有为绘图而关闭系统中断或重设 LCD 模式。
