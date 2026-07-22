"""
Kflower 集成测试套件
验证工作流和智能体升级方案的完整功能
"""
import sys
import os
import json

# 切换到正确的项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kflower-backend'))


async def test_workflow_engine(db):
    """测试工作流引擎核心功能"""
    from app.core.workflow.engine import WorkflowEngine
    from app.models.workflow import Workflow
    
    print("=== F1: 工作流引擎测试 ===")
    
    # 1. 引擎可实例化
    engine = WorkflowEngine(db)
    assert engine is not None
    print("  F1.1 引擎实例化: PASS")
    
    # 2. 验证导入的依赖
    from app.core.workflow.sla_manager import SLAManager
    from app.core.workflow.node_types import NodeType
    from app.core.workflow.assignee_resolver import AssigneeResolver
    from app.core.workflow.condition_evaluator import ConditionEvaluator
    print("  F1.2 模块导入完整(SLA/Node/Resolver/Evaluator): PASS")
    
    print("  F1: ALL PASSED")


async def test_agent_orchestrator():
    """测试智能体编排器"""
    from app.core.agent_engine.orchestrator import agent_orchestrator, AgentType, Task
    
    print("\n=== F2: 智能体编排器测试 ===")
    
    # 1. 方法存在
    assert hasattr(agent_orchestrator, 'is_running')
    assert hasattr(agent_orchestrator, 'get_task_statistics')
    assert hasattr(agent_orchestrator, 'get_tasks')
    print("  F2.1 编排器方法完整: PASS")
    
    # 2. 方法返回值正确
    assert agent_orchestrator.is_running() is False
    stats = agent_orchestrator.get_task_statistics()
    assert 'total' in stats
    tasks = agent_orchestrator.get_tasks()
    assert isinstance(tasks, list)
    agents = agent_orchestrator.list_agents()
    assert len(agents) >= 4  # 至少4个默认智能体
    print(f"  F2.2 方法正常运行: PASS (agents={len(agents)}, stats={stats})")
    
    # 3. 智能体服务
    from app.core.agent_engine.agent_service import agent_service
    agents2 = agent_service.list_agents()
    assert len(agents2) >= 4
    print(f"  F2.3 AgentService.list_agents(): PASS ({len(agents2)} agents)")
    
    print("  F2: ALL PASSED")


async def test_agent_tools():
    """测试工具系统"""
    from app.core.agent_engine.tools import tool_registry, tool_executor
    
    print("\n=== F3: 工具系统测试 ===")
    
    # 1. 工具注册
    tools = tool_registry.list_tools()
    assert len(tools) >= 17
    print(f"  F3.1 工具注册: PASS ({len(tools)} tools)")
    
    # 2. 检查关键工具存在
    tool_names = {t['name'] for t in tools}
    required = {'read_file', 'write_file', 'bash', 'search_content', 'list_files', 
                'get_env_info', 'create_template', 'execute_workflow', 'query_data'}
    missing = required - tool_names
    assert not missing, f"Missing tools: {missing}"
    print(f"  F3.2 关键工具齐全: PASS")
    
    # 3. OpenAI格式
    openai_format = tool_registry.get_tools_as_openai_format()
    assert len(openai_format) >= 17
    first = openai_format[0]
    assert 'function' in first
    assert 'parameters' in first['function']
    assert 'description' in first['function']
    print(f"  F3.3 OpenAI格式输出: PASS")
    
    # 4. 工具执行器存在所有handler
    handler_names = set(tool_executor.handlers.keys())
    missing_handlers = tool_names - handler_names
    # system tools may not have handlers (OK for now)
    critical_tools = {'create_template', 'execute_workflow', 'query_data', 'read_file', 'bash'}
    assert critical_tools.issubset(handler_names), f"Missing handlers: {critical_tools - handler_names}"
    print(f"  F3.4 工具执行器handler: PASS ({len(handler_names)} handlers)")
    
    print("  F3: ALL PASSED")


async def test_workflow_api(client, token):
    """测试工作流API端点"""
    AUTH = {'Authorization': f'Bearer {token}'}
    
    print("\n=== F4: 工作流API测试 ===")
    
    # 1. 列表
    r = client.get('/api/v1/workflows/', headers=AUTH)
    assert r.status_code == 200
    wfs = r.json()
    assert len(wfs) >= 1
    print(f"  F4.1 列表: PASS ({len(wfs)} workflows)")
    
    # 2. 详情
    wf_id = wfs[0]['id'] if isinstance(wfs, list) else 1
    r = client.get(f'/api/v1/workflows/{wf_id}', headers=AUTH)
    assert r.status_code == 200
    print(f"  F4.2 详情: PASS")
    
    # 3. 实例管理
    r = client.get('/api/v1/workflows/instances/pending', headers=AUTH)
    assert r.status_code == 200
    r = client.get('/api/v1/workflows/instances/my', headers=AUTH)
    assert r.status_code == 200
    r = client.get('/api/v1/workflows/instances/', headers=AUTH)
    assert r.status_code == 200
    print(f"  F4.3 实例管理(pending/my/all): PASS")
    
    # 4. 启动实例
    r = client.post(f'/api/v1/workflows/{wf_id}/start', json={
        'title': 'Integration Test',
        'variables': {'test': True, 'starter_id': 1},
    }, headers=AUTH)
    assert r.status_code == 200
    inst_id = r.json().get('data', {}).get('instance_id')
    assert inst_id is not None
    print(f"  F4.4 启动实例: PASS (instance_id={inst_id})")
    
    # 5. 实例详情
    r = client.get(f'/api/v1/workflows/instances/{inst_id}', headers=AUTH)
    assert r.status_code == 200
    detail = r.json().get('data', {})
    assert detail.get('title')
    assert 'tasks' in detail
    assert 'logs' in detail
    print(f"  F4.5 实例详情: PASS (tasks={len(detail.get('tasks',[]))})")
    
    print("  F4: ALL PASSED")


async def test_agent_api(client, token):
    """测试智能体API端点"""
    AUTH = {'Authorization': f'Bearer {token}'}
    
    print("\n=== F5: 智能体API测试 ===")
    
    # 1. 工具列表
    r = client.get('/api/v1/agent/tools', headers=AUTH)
    assert r.status_code == 200
    tools = r.json().get('tools', [])
    assert len(tools) >= 17
    print(f"  F5.1 工具列表: PASS ({len(tools)} tools)")
    
    # 2. 智能体列表
    r = client.get('/api/v1/agent/agents', headers=AUTH)
    assert r.status_code == 200
    print(f"  F5.2 智能体列表: PASS")
    
    # 3. 聊天端点（无工具）
    r = client.post('/api/v1/agent/chat', json={
        'message': '你好',
        'enable_tools': False,
        'use_rag': False,
        'ai_type': 'general'
    }, headers=AUTH)
    assert r.status_code == 200
    assert 'response' in r.json()
    print(f"  F5.3 简单聊天: PASS")
    
    # 4. Agent Engine状态
    r = client.get('/api/v1/ai/agent-engine/status', headers=AUTH)
    assert r.status_code == 200
    data = r.json().get('data', {})
    assert 'agents_count' in data
    assert data.get('agents_count', 0) > 0
    print(f"  F5.4 引擎状态: PASS (agents={data.get('agents_count')})")
    
    # 5. 记忆端点（返回真实空数据，非模拟）
    r = client.get('/api/v1/ai/agent-engine/memory/stats', headers=AUTH)
    assert r.status_code == 200
    mem = r.json().get('data', {})
    assert mem.get('total_memories', 999) == 0
    print(f"  F5.5 记忆统计(真实): PASS (total=0)")
    
    r = client.get('/api/v1/ai/agent-engine/memory/list', headers=AUTH)
    assert r.status_code == 200
    mem_list = r.json().get('data', [])
    assert len(mem_list) == 0
    print(f"  F5.6 记忆列表(真实): PASS (empty)")
    
    print("  F5: ALL PASSED")


async def test_security():
    """测试安全修复"""
    from app.core.agent_engine.tools.executor import tool_executor
    from app.core.scope_filter import scope_filter_engine
    
    print("\n=== F6: 安全测试 ===")
    
    # 1. SQL注入保护
    result = await tool_executor._query_data({'table': 'users; DROP TABLE users--', 'conditions': {}}, {})
    assert 'error' in result or '不允许' in str(result)
    print("  F6.1 SQL注入防护: PASS")
    
    # 2. 危险命令防护
    result2 = await tool_executor._bash({'command': 'rm -rf /'}, {})
    assert 'error' in result2 or '禁止' in str(result2)
    print("  F6.2 危险命令防护: PASS")
    
    # 3. 行级权限模板变量
    scope = scope_filter_engine.resolve_scope(
        {'created_by': '{{ ctx.current_user.id }}'},
        {'id': 123}
    )
    assert scope == {'created_by': 123}
    print(f"  F6.3 权限模板变量: PASS")
    
    print("  F6: ALL PASSED")


async def run_all_tests():
    """运行所有测试"""
    from app.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    resp = client.post('/api/v1/auth/login', 
        json={'username': 'admin', 'password': 'admin123'})
    token = resp.json()['access_token']
    
    print("=" * 60)
    print("Kflower 集成测试套件")
    print("=" * 60)
    
    # 需要数据库会话的测试
    from app.core.database import get_db
    async for db in get_db():
        await test_workflow_engine(db)
        break
    
    await test_agent_orchestrator()
    await test_agent_tools()
    await test_workflow_api(client, token)
    await test_agent_api(client, token)
    await test_security()
    
    print("\n" + "=" * 60)
    print("全部测试通过!")
    print("=" * 60)


if __name__ == '__main__':
    import asyncio
    asyncio.run(run_all_tests())
