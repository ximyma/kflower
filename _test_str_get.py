"""验证字符串没有 .get() 方法"""
s = '{"access_type":"private"}'
print(f"type: {type(s)}")
try:
    result = s.get('table_name', 'default')
    print(f"result: {result}")
except AttributeError as e:
    print(f"AttributeError: {e}")
