#include "bbk7980.h"
unsigned char buffer[600],readback[600];
volatile unsigned char phase,handle,status,ok,id;
volatile unsigned int wrote,read_count;
volatile unsigned long length;
volatile unsigned char edge_flags;
volatile unsigned char edge_status[8];
static void edge_tests(void) {
    unsigned char h,good;
    unsigned int i;
    edge_flags=0;
    h=bbk_file_open("SDKTEST.DAT",BBK_OPEN_UPDATE);
    if(h!=255) {
        good=bbk_file_seek(h,510,0)==0 && bbk_file_write(h,"PATCH",5)==5;
        good=bbk_file_close(h)==0 && good;
        id=bbk_file_find("SDKTEST.DAT");length=bbk_file_size(id);
        read_count=bbk_file_read_at(id,0,readback,600);
        for(i=0;i<600;i++)if(readback[i]!=(i>=510 && i<515?(unsigned char)"PATCH"[i-510]:(unsigned char)(i*37+11)))good=0;
        if(good && length==600 && read_count==600)edge_flags|=1;
    }
    h=bbk_file_open("SDKTEST.DAT",BBK_OPEN_CREATE);
    if(h==255 && bbk_file_error()==2)edge_flags|=2;
    h=bbk_file_open("SDKTEST.DAT",BBK_OPEN_READ);
    edge_status[0]=h;edge_status[1]=bbk_file_error();
    if(h!=255) {
        good=bbk_file_write(h,"x",1)==BBK_READ_ERROR;
        edge_status[2]=good;edge_status[3]=bbk_file_error();
        edge_status[4]=bbk_file_close(h);
        if(edge_status[4]==0 && good)edge_flags|=4;
    }
    h=bbk_file_open("SDKTEST.DAT",BBK_OPEN_REPLACE);
    if(h!=255) {
        good=bbk_file_write(h,"short",5)==5;
        good=bbk_file_close(h)==0 && good;
        id=bbk_file_find("SDKTEST.DAT");length=bbk_file_size(id);
        if(good && length==5)edge_flags|=8;
    }
    h=bbk_file_open("SDKDELETE.DAT",BBK_OPEN_CREATE);
    if(h!=255) {
        good=bbk_file_write(h,"delete",6)==6;
        good=bbk_file_close(h)==0 && good;
        good=bbk_file_delete("SDKDELETE.DAT")==0 && good;
        if(bbk_file_find("SDKDELETE.DAT")==255 && good)edge_flags|=16;
    }
    h=bbk_file_open("SDKTEST.DAT",BBK_OPEN_UPDATE);
    if(h!=255) {
        good=bbk_file_seek(h,2,0)==0 && bbk_file_seek(h,1,1)==0 && bbk_file_write(h,"!",1)==1;
        good=bbk_file_seek(h,0,2)==0 && bbk_file_write(h,"+",1)==1 && good;
        good=bbk_file_close(h)==0 && good;
        id=bbk_file_find("SDKTEST.DAT");length=bbk_file_size(id);read_count=bbk_file_read_at(id,0,readback,8);
        for(i=0;i<6;i++)if(readback[i]!=(unsigned char)"sho!t+"[i])good=0;
        if(good && length==6 && read_count==6)edge_flags|=32;
    }
}
int main(void) {
    bbk_event event;
    unsigned int i;
    bbk_fill(0,0,240,120,0);
    bbk_text_gbk(8,8,"\xce\xc4\xbc\xfe\xd0\xb4\xc8\xeb",16,3);
    phase=1;handle=bbk_file_open("SDKTEST.DAT",BBK_OPEN_REPLACE);
    if(handle==255){status=bbk_file_error();goto wait;}
    for(i=0;i<600;i++)buffer[i]=(unsigned char)(i*37+11);
    phase=2;wrote=bbk_file_write(handle,buffer,600);status=bbk_file_close(handle);
    phase=3;id=bbk_file_find("SDKTEST.DAT");length=bbk_file_size(id);
    read_count=bbk_file_read_at(id,0,readback,600);
    ok=status==0 && wrote==600 && read_count==600 && length==600;
    for(i=0;i<600;i++)if(buffer[i]!=readback[i])ok=0;
    phase=4;
    bbk_fill(8,40,224,24,ok?1:3);
wait:
    while(bbk_event_wait(&event))if(event.type==BBK_EVENT_KEY) {
        if(event.value==BBK_KEY_ESC)break;
        if(event.value==BBK_KEY_F1)edge_tests();
    }
    bbk_keys_flush();return 0;
}
