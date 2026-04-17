# -*- coding: utf-8 -*-
"""
在后端添加模板发布接口
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-backend\app\api\v1\endpoints\templates.py'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 在文件末尾添加发布接口
publish_endpoint = '''

@router.post("/{template_id}/publish")
async def publish_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发布模板 - 使模板可供组织内其他用户使用"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查权限：只有创建者可以发布
    if template.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="只有模板创建者可以发布")
    
    # 设置为已发布
    template.is_published = True
    template.organization_id = current_user.organization_id
    
    await db.commit()
    await db.refresh(template)
    
    return BaseResponse(
        success=True,
        message="模板已发布",
        data={"template_id": template.id, "is_published": True}
    )
'''

if '@router.post("/{template_id}/publish")' not in content:
    content = content.rstrip() + publish_endpoint
    print("[OK] 发布接口已添加")
else:
    print("[INFO] 发布接口已存在")

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\n后端发布接口添加完成！")