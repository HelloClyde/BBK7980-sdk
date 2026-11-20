"""BBK7980 experimental desktop emulator; the screen is rendered by stock firmware."""
import argparse
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from machine import Machine, ROOT, APP_DIR
from keyboard import KEYS
from audio_output import AudioOutput

PALETTE=[235,241,220,153,169,131,83,105,65,26,45,25]+[0]*756

class Emulator:
    def __init__(self, window, options):
        self.window=window;self.options=options;self.running=True;self.pressed=set()
        self.window.title('步步高 7980 模拟器 · 实验版 0.4')
        self.window.configure(bg='#e8e8e2');self.window.resizable(False,False)
        self.machine=Machine();self.data_dir=APP_DIR/'data';self.data_dir.mkdir(exist_ok=True)
        self.audio_output=AudioOutput()
        self.save_path=self.data_dir/'nand.bin';self.closed=False
        preset=ROOT/'runtime/minesweeper-nand.bin.z'
        if not preset.exists():preset=ROOT/'runtime/installed-nand.bin.z'
        source=Path(options.nand) if options.nand else self.save_path if self.save_path.exists() else preset
        self.machine.load_nand(source)
        outer=ttk.Frame(window,padding=16);outer.pack()
        ttk.Label(outer,text='BBK 7980',font=('Segoe UI',20,'bold')).pack(anchor='w')
        ttk.Label(outer,text='原厂 V1.10 系统 · 240 × 120 · 四级灰度').pack(anchor='w',pady=(0,12))
        self.screen=tk.Label(outer,bg='#35462d',bd=8,relief='sunken');self.screen.pack()
        self.font_notice=tk.StringVar(value='正在检查中文字库…')
        ttk.Label(outer,textvariable=self.font_notice,foreground='#805127').pack(pady=8)
        row=ttk.Frame(outer);row.pack(pady=4)
        for i in range(5):self.key_button(row,f'F{i+1}',44+i).pack(side='left',padx=4)
        row=ttk.Frame(outer);row.pack(pady=4)
        for label,code in [('上',57),('下',59),('左',51),('右',58),('确定 ↵',50),('返回 Esc',49),('主菜单',52),('帮助',55),('上一栏',42),('下一栏',43)]:
            self.key_button(row,label,code).pack(side='left',padx=3)
        row=ttk.Frame(outer);row.pack(pady=8)
        for label,action in [('暂停 / 继续',self.pause),('重启',self.reset),('保存',self.save),('截图',self.screenshot),('载入 NAND',self.open_nand),('按键矩阵',self.matrix)]:
            ttk.Button(row,text=label,command=action).pack(side='left',padx=3)
        self.status=tk.StringVar(value='正在启动…');ttk.Label(outer,textvariable=self.status).pack(anchor='w',pady=(8,0))
        window.bind('<KeyPress>',self.key_down);window.bind('<KeyRelease>',self.key_up)
        window.bind('<FocusOut>',lambda event:self.release_all())
        window.protocol('WM_DELETE_WINDOW',self.close)
        self.machine.run(80_000_000);self.update_font_notice()
        if options.minesweeper:self.launch_minesweeper()
        if hasattr(self.machine.lib,'bbk_audio_clear'):self.machine.lib.bbk_audio_clear()
        self.last_frame=None;self.render()
        window.after(16,self.step)
        if options.smoke_test:window.after(500,self.smoke_test)

    def key_button(self,parent,label,code):
        button=ttk.Button(parent,text=label,width=max(5,len(label)+1),takefocus=False)
        button.bind('<ButtonPress-1>',lambda event:self.press(code))
        button.bind('<ButtonRelease-1>',lambda event:self.release(code))
        return button

    def press(self,code):
        if code not in self.pressed:
            self.pressed.add(code);self.machine.lib.bbk_key(code//8,code%8,1)

    def release(self,code):
        self.pressed.discard(code);self.machine.lib.bbk_key(code//8,code%8,0)

    def release_all(self):
        for code in list(self.pressed):self.release(code)

    def key_down(self,event):
        if event.keysym in KEYS:self.press(KEYS[event.keysym])

    def key_up(self,event):
        if event.keysym in KEYS:self.release(KEYS[event.keysym])

    def frame_image(self):
        im=Image.frombytes('P',(240,120),self.machine.frame());im.putpalette(PALETTE)
        return im.convert('RGB')

    def render(self):
        frame=self.machine.frame()
        if frame!=self.last_frame:
            self.last_frame=frame;im=Image.frombytes('P',(240,120),frame);im.putpalette(PALETTE)
            self.photo=ImageTk.PhotoImage(im.resize((720,360),Image.Resampling.NEAREST));self.screen.configure(image=self.photo)

    def step(self):
        if self.closed:return
        if self.running:self.machine.run(66_667)
        self.audio_output.write(self.machine.audio())
        self.render();s=self.machine.state()
        self.status.set(f'{"运行中" if self.running else "已暂停"} · PC {s["pc"]:04X} · {s["cycles"]/4_000_000:.1f} 秒 · 方向键 / Enter / Esc / F1–F5')
        self.window.after(16,self.step)

    def pause(self):
        self.running=not self.running;self.release_all()
        if not self.running:self.audio_output.clear()
    def update_font_notice(self):
        text='兼容中文字库已启用。' if self.machine.lib.bbk_read(0x9eca)!=0xff else '当前镜像缺少中文字库，部分汉字显示为方块。'
        self.font_notice.set(text+(' PSG 旋律声音已启用；语音尚未实现。' if self.audio_output.available else ' 当前音频设备不可用。'))

    def reset(self):
        self.release_all();self.machine.lib.bbk_reset();self.machine.run(80_000_000);self.update_font_notice()
        if self.options.minesweeper:self.launch_minesweeper()
        self.audio_output.clear()
        if hasattr(self.machine.lib,'bbk_audio_clear'):self.machine.lib.bbk_audio_clear()

    def launch_minesweeper(self):
        # Drive the real shell and loader, including their normal file checks.
        for code in [43]*8+[6]:
            self.machine.lib.bbk_key(code//8,code%8,1);self.machine.run(300_000)
            self.machine.lib.bbk_key(code//8,code%8,0);self.machine.run(30_000_000 if code==6 else 5_000_000)

    def save(self):
        try:self.machine.save_nand(self.save_path);self.status.set('已保存到 '+str(self.save_path))
        except OSError as exc:messagebox.showerror('保存失败',str(exc))

    def screenshot(self):
        path=filedialog.asksaveasfilename(defaultextension='.png',filetypes=[('PNG 图片','*.png')])
        if path:self.frame_image().resize((960,480),Image.Resampling.NEAREST).save(path)

    def open_nand(self):
        path=filedialog.askopenfilename(filetypes=[('NAND 镜像','*.bin *.z'),('所有文件','*')])
        if not path:return
        try:self.machine.load_nand(path);self.reset()
        except (OSError,ValueError) as exc:messagebox.showerror('载入失败',str(exc))

    def matrix(self):
        panel=tk.Toplevel(self.window);panel.title('7980 原始按键矩阵')
        ttk.Label(panel,text='Y = 16；Esc = 49；Enter = 50；帮助 = 55；Delete = 56。').grid(row=0,column=0,columnspan=8,padx=10,pady=10)
        for code in range(64):self.key_button(panel,f'{code:02d}',code).grid(row=code//8+1,column=code%8,padx=3,pady=3)

    def smoke_test(self):
        before=self.machine.frame()
        code=50 if self.options.minesweeper else 43
        self.press(code);self.machine.run(8_000_000);self.release(code);self.render()
        if before==self.machine.frame():raise RuntimeError('Guest did not respond to its input')
        target=Path(self.options.smoke_test);target.parent.mkdir(parents=True,exist_ok=True)
        self.frame_image().save(target)
        self.window.update()
        from PIL import ImageGrab
        x,y=self.window.winfo_rootx(),self.window.winfo_rooty()
        width,height=self.window.winfo_width(),self.window.winfo_height()
        ImageGrab.grab(bbox=(x,y,x+width,y+height)).save(target.with_name(target.stem+'-window.png'))
        self.audio_output.close();self.closed=True;self.window.destroy()

    def close(self):
        self.release_all()
        try:self.machine.save_nand(self.save_path)
        except OSError as exc:
            messagebox.showerror('保存失败',str(exc));return
        self.audio_output.close();self.closed=True;self.window.destroy()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--nand');parser.add_argument('--smoke-test');parser.add_argument('--minesweeper',action='store_true')
    args=parser.parse_args();window=tk.Tk();Emulator(window,args);window.mainloop()
