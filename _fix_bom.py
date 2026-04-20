import os

files_to_fix = [
    r'E:\kkflower\kflower-backend\app\api\v1\endpoints\templates.py',
    r'E:\kkflower\kflower-backend\app\core\ai_digital_base\gateway.py',
    r'E:\kkflower\kflower-backend\app\core\ai_digital_base\local_services.py',
    r'E:\kkflower\kflower-backend\app\core\ai_digital_base\model_manager.py',
    r'E:\kkflower\kflower-backend\app\core\ai_digital_base\__init__.py',
]

for fpath in files_to_fix:
    with open(fpath, 'rb') as f:
        content = f.read()

    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]  # Remove BOM
        with open(fpath, 'wb') as f:
            f.write(content)
        print(f'Removed BOM: {fpath}')
    else:
        print(f'No BOM: {fpath}')

print('Done')
