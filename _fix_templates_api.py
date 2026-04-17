# -*- coding: utf-8 -*-
path = r'D:\kflower\kflower-backend\app\api\v1\endpoints\templates.py'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Fix 1: list_templates should show all templates (not just published)
old_list = """async def list_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    \"\"\"获取模板列表\"\"\"
    query = select(Template).where(Template.is_published == True)"""

new_list = """async def list_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    \"\"\"获取模板列表 - 显示所有模板（自己创建的 + 已发布的）\"\"\"
    # 显示所有模板：自己创建的 + 组织内已发布的
    query = select(Template).where(
        (Template.created_by == current_user.id) | 
        (Template.is_published == True)
    )"""

if old_list in content:
    content = content.replace(old_list, new_list)
    print("Fixed list_templates filter")
else:
    print("Pattern 1 not found")

# Fix 2: create_template should default is_published to True
old_create = """template = Template(
        name=request.name,
        code=code,
        description=request.description,
        category=request.category,
        modules=[m.dict() for m in request.modules],
        ai_generated=request.ai_generated,
        ai_prompt=request.ai_prompt,
        organization_id=current_user.organization_id,
        created_by=current_user.id
    )"""

new_create = """template = Template(
        name=request.name,
        code=code,
        description=request.description,
        category=request.category,
        modules=[m.dict() for m in request.modules] if request.modules else [],
        ai_generated=request.ai_generated,
        ai_prompt=request.ai_prompt,
        is_published=True,  # 默认发布，这样创建后就能看到
        organization_id=current_user.organization_id,
        created_by=current_user.id
    )"""

if old_create in content:
    content = content.replace(old_create, new_create)
    print("Fixed create_template default is_published")
else:
    print("Pattern 2 not found")

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("Done")