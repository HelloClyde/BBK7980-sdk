"""Real guest launch, APIs, IRQ coexistence, Minesweeper win/loss and shell return."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

SDK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SDK/'tools'))
from emulator import install

def validate(emulator):
    emulator=Path(emulator).resolve();out=SDK/'build/validation';out.mkdir(parents=True,exist_ok=True)
    from emulator_backend import prepare
    prepare(emulator)
    applications=[SDK/'examples'/name/'build'/file for name,file in [('minesweeper','扫雷.exe'),('hello','开发演示.exe'),('diagnostics','开发自检.exe')]]
    m,installed=install(emulator,emulator/'runtime/installed-nand.bin.z',applications,out/'sdk-nand.bin.z')
    from capture_games import tap,menu,PALETTE
    from PIL import Image
    checks=[]
    def require(value,label):
        if not value:raise AssertionError(label)
        checks.append(label)
    def symbols(name):return json.loads((SDK/'examples'/name/'build/build.json').read_text(encoding='utf8'))['symbols']
    def rd(s,name,size=1):return sum(m.lib.bbk_read(s['_'+name]+i)<<(8*i) for i in range(size))
    def data(address,size):return bytes(m.lib.bbk_read(address+i) for i in range(size))
    def snapshot(name):
        im=Image.frombytes('P',(240,120),m.frame());im.putpalette(PALETTE)
        im.resize((960,480),Image.Resampling.NEAREST).convert('RGB').save(out/(name+'.png'))
    def launch(index):menu(m);tap(m,index,40_000_000)
    def exit_app():
        tap(m,49,30_000_000)
        require(m.state()['flags']&1 and not m.state()['p']&4,'Esc returns to OS event wait with IRQ enabled')
    launch(8);s=symbols('diagnostics')
    require(rd(s,'sdk_ready')==1 and rd(s,'canary_ok')==1,'C initialized DATA and BSS/stack coexist with IRQs')
    require(rd(s,'stress_sum',2)==sum(i^0x5a5a for i in range(10000))&65535,'C arithmetic survives interrupts')
    require(rd(s,'font_ok')==7,'Original glyph service reads 12/16/24-dot characters')
    font=(emulator/'runtime/font.bin').read_bytes();expected=b''
    for base,size in [(0,24),(0x8d030,32),(0x149070,72)]:
        offset=base+((0xd6-0x81)*191+0xd0-0x40)*size;expected+=font[offset:offset+size]
    require(data(s['_font_buffer'],128)==expected,'All three native glyph byte sequences match font file')
    require(rd(s,'file_id')!=255 and rd(s,'missing_id')==255,'Native file lookup accepts ROM string literals and missing files')
    require(rd(s,'file_size',4)==len(font),'Native file size returns 32-bit length')
    require(rd(s,'file_read',2)==600 and data(s['_file_buffer'],600)==font[500:1100],'Native file read crosses NAND page boundaries')
    require(rd(s,'file_edges_ok')==1 and data(s['_edge_buffer'],6)==font[-6:],'File reader clamps EOF and rejects invalid IDs')
    before=m.state();periodic=rd(s,'periodic_count');m.run(20_000_000)
    require(m.state()['interrupts']>before['interrupts']+100 and rd(s,'periodic_count')>periodic,'OS IRQs and periodic events continue while C application waits')
    rom=(emulator/'runtime/syscode.bin').read_bytes()
    for code in [50,58,34,40]:
        tap(m,code,3_000_000)
        offset=0xc000+(0x7d67-0x4000)+code*2
        logical=rom[offset+1]
        require(rd(s,'last_key')==code and rd(s,'translated_value',2)==logical and rd(s,'translated_type')==rom[offset],'Native keyboard event and logical translation '+str(code))
    require(not m.state()['p']&4,'Application event wait leaves CPU IRQs enabled');exit_app()
    launch(7);s=symbols('hello');snapshot('hello')
    x=rd(s,'x');tap(m,58,5_000_000)
    require(rd(s,'x')==x+8,'Hello example uses initialized DATA and native keyboard input');exit_app()
    launch(6);s=symbols('minesweeper');snapshot('minesweeper-ready')
    base=s['_game'];cursor=s['_cursor']
    def game():return dict(state=m.lib.bbk_read(base+194),opened=m.lib.bbk_read(base+195),flags=m.lib.bbk_read(base+196),placed=m.lib.bbk_read(base+197))
    def board():return list(data(base,96))
    def key(code,settle=8_000_000):tap(m,code,settle)
    def move(target):
        for _ in range(32):
            current=m.lib.bbk_read(cursor)
            if current==target:return
            code=59 if current//12<target//12 else 57 if current//12>target//12 else 58 if current%12<target%12 else 51
            key(code,2_000_000)
        raise AssertionError('Cursor movement')
    require(game()==dict(state=0,opened=0,flags=0,placed=0),'SDK Minesweeper launches through original shell')
    key(34);require(game()['flags']==1,'Flag placement through OS keyboard event')
    key(50);require(game()['placed']==0,'Flag protects first cell')
    key(34);key(50,20_000_000);cells=board()
    require(game()['state']==1 and game()['opened']>1 and sum(bool(v&128) for v in cells)==15,'First click, flood reveal and 15 mines')
    require(all(not cells[i]&128 for i in (0,1,12,13)),'First click neighborhood is safe')
    snapshot('minesweeper-playing')
    # Force drawing work and inspect actual SDK instructions, excluding OS IRQ context.
    m.lib.bbk_key(44//8,44%8,1);observed=0;irq_before=m.state()['interrupts']
    for _ in range(180000):
        pc=m.lib.bbk_pc();flags=m.lib.bbk_flags()
        bank=m.lib.bbk_read(0x32)|(m.lib.bbk_read(0x33)<<8)
        if bank==0x120 and 0x4000<=pc<0x8000 and not flags&4:
            require_irq=not m.lib.bbk_reg(5)&4
            if not require_irq:raise AssertionError('SDK executed with IRQ mask set at '+hex(pc))
            observed+=1
        m.run(1)
    m.lib.bbk_key(44//8,44%8,0);m.run(8_000_000)
    require(observed>3000 and m.state()['interrupts']>irq_before,'Active C drawing/input executes with IRQ enabled; system IRQs are serviced')
    # The flag used for stress may cover a safe square; restart before game checks.
    key(40,20_000_000);key(50,20_000_000);cells=board()
    mine=next(i for i,v in enumerate(cells) if v&128);move(mine);key(50)
    require(game()['state']==2,'Mine triggers loss');snapshot('minesweeper-lost')
    key(40,20_000_000);require(game()['state']==0 and not game()['placed'],'N restarts')
    key(50,20_000_000)
    for pos in range(96):
        if game()['state']==3:break
        if not board()[pos]&(128|16):move(pos);key(50)
    require(game()==dict(state=3,opened=81,flags=15,placed=1),'Win opens all 81 safe cells and flags 15 mines')
    snapshot('minesweeper-won');exit_app();snapshot('returned-to-system')
    # Re-entry proves the bridge and C initializer do not rely on a previous app run.
    launch(7);s=symbols('hello');require(rd(s,'x')==112 and rd(s,'y')==66,'C DATA reinitializes on a second launch');exit_app()
    launch(7);tap(m,52,30_000_000)
    require(m.state()['flags']&1 and not m.state()['p']&4,'Native Home handling returns to shell with IRQs enabled')
    report=dict(result='passed',checks=checks,sdk_instruction_samples=observed,installed=installed,final_cpu=m.state(),
                firmware_sha256=hashlib.sha256((emulator/'runtime/syscode.bin').read_bytes()).hexdigest())
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--emulator',type=Path,required=True)
    validate(p.parse_args().emulator)
