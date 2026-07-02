#!/bin/bash
# Create a test image
python3 -c "
import struct, zlib
sig = b'\x89PNG\r\n\x1a\n'
def chunk(ctype, data):
    c = ctype + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
ihdr = struct.pack('>IIBBBBB', 10, 10, 8, 2, 0, 0, 0)
raw = b'\x00' + b'\xff\x00\x00' * 10
for _ in range(9):
    raw += b'\x00' + b'\xff\x00\x00' * 10
idat = zlib.compress(raw)
with open('/tmp/test_upload.png', 'wb') as f:
    f.write(sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b''))
print('Test image created')
"

# Upload to media service
echo "Uploading..."
curl -s -X POST http://localhost:8097/upload \
  -F "file=@/tmp/test_upload.png" \
  -F "media_type=image" | python3 -m json.tool
