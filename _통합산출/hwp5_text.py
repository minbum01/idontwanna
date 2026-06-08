# -*- coding: utf-8 -*-
"""HWP5(OLE2) 본문 텍스트 추출. 원본 읽기 전용."""
import olefile, zlib, struct, sys

PARA_TEXT = 67  # HWPTAG_BEGIN(16)+51

# 확장 컨트롤(8 wchar=16바이트 차지)
EXT_CTRL = {1,2,3,4,11,12,14,15,16,17,18,21,22,23}
# 인라인/문자 컨트롤(1 wchar)
INLINE_CTRL = {0,10,13,24,25,26,27,28,29,30,31}

def para_text(payload):
    out=[]
    i=0
    n=len(payload)
    while i+1 < n:
        wc = payload[i] | (payload[i+1]<<8)
        if wc in EXT_CTRL:
            i += 16
            continue
        if wc in INLINE_CTRL:
            if wc in (10,13): out.append('\n')
            i += 2
            continue
        out.append(chr(wc))
        i += 2
    return ''.join(out)

def extract(path):
    ole = olefile.OleFileIO(path)
    # 압축 여부
    hdr = ole.openstream('FileHeader').read()
    compressed = bool(hdr[36] & 1)
    # 섹션 스트림 수집
    secs=[]
    for entry in ole.listdir():
        if len(entry)==2 and entry[0]=='BodyText' and entry[1].lower().startswith('section'):
            secs.append('/'.join(entry))
    def key(s):
        import re
        m=re.search(r'(\d+)$',s); return int(m.group(1)) if m else 0
    secs.sort(key=key)
    texts=[]
    for s in secs:
        data = ole.openstream(s).read()
        if compressed:
            data = zlib.decompress(data, -15)
        pos=0; L=len(data)
        while pos+4 <= L:
            header = struct.unpack('<I', data[pos:pos+4])[0]
            tag = header & 0x3ff
            size = (header>>20) & 0xfff
            pos+=4
            if size == 0xfff:
                size = struct.unpack('<I', data[pos:pos+4])[0]; pos+=4
            payload = data[pos:pos+size]; pos+=size
            if tag == PARA_TEXT:
                texts.append(para_text(payload))
    ole.close()
    return '\n'.join(texts)

if __name__ == '__main__':
    print(extract(sys.argv[1]))
