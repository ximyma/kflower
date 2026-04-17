# -*- coding: utf-8 -*-
import os, glob, re

base = r'D:\kflower\kflower-frontend\src\common\pc\views'
for fpath in glob.glob(os.path.join(base, '*.vue')):
    with open(fpath, 'rb') as f:
        content = f.read()
    orig = content
    
    # Fix Copy -> CopyDocument in imports and usage
    content = re.sub(rb'\bCopy\b(?!Document)', b'CopyDocument', content)
    
    # Fix any double DocumentCopies
    content = content.replace(b'CopyDocumentDocument', b'CopyDocument')
    
    if content != orig:
        with open(fpath, 'wb') as f:
            f.write(content)
        print(f'Fixed: {os.path.basename(fpath)} ({len(content)} bytes)')
    else:
        print(f'OK: {os.path.basename(fpath)}')
print('Done.')
