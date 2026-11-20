"""Create a minimal SDK project without modifying an existing directory."""
from pathlib import Path
import argparse
import json

TEMPLATE='''#include "bbk7980.h"
int main(void) {
    bbk_event event;
    bbk_fill(0,0,240,120,0);
    bbk_fill(24,24,192,72,1);
    while(bbk_event_wait(&event)) {
        if(event.type==BBK_EVENT_KEY && event.value==BBK_KEY_ESC)break;
    }
    bbk_keys_flush();return 0;
}
'''
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--name',default='新应用')
    a=p.parse_args();name=a.name.encode('gbk')
    if not name or len(name)>8 or any(c in a.name for c in '/\\:\0'):p.error('Name must fit 8 GBK bytes and contain no path separator')
    a.directory.mkdir(parents=True,exist_ok=False)
    (a.directory/'main.c').write_text(TEMPLATE,encoding='utf8')
    (a.directory/'project.json').write_text(json.dumps(dict(name=a.name,category=9,sources=['main.c']),ensure_ascii=False,indent=2),encoding='utf8')
    print(a.directory.resolve())
