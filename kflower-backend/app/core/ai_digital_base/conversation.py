"""
AI数字底座 - 对话管理模块
管理AI对话上下文和历史记录
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from app.core.ai_digital_base.gateway import ai_gateway


class ConversationManager:
    """
    对话管理器
    管理多轮对话上下文，支持对话历史、摘要等
    """
    
    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
    
    def create_conversation(self, conversation_id: str, metadata: Optional[Dict] = None) -> None:
        """创建新对话"""
        self.conversations[conversation_id] = []
        self.metadata[conversation_id] = metadata or {}
        self.metadata[conversation_id]["created_at"] = datetime.now().isoformat()
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """添加消息到对话"""
        if conversation_id not in self.conversations:
            self.create_conversation(conversation_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if metadata:
            message["metadata"] = metadata
        
        self.conversations[conversation_id].append(message)
        
        # 限制历史长度
        if len(self.conversations[conversation_id]) > self.max_history:
            # 保留系统消息和最新的消息
            self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_history:]
    
    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取对话消息"""
        return self.conversations.get(conversation_id, [])
    
    def get_history_for_ai(self, conversation_id: str, max_turns: int = 10) -> List[Dict[str, str]]:
        """获取发送给AI的对话历史"""
        messages = self.get_messages(conversation_id)
        if not messages:
            return []
        
        # 截取最近的消息
        recent_messages = messages[-max_turns * 2:] if len(messages) > max_turns * 2 else messages
        return [{"role": m["role"], "content": m["content"]} for m in recent_messages]
    
    def clear_conversation(self, conversation_id: str) -> None:
        """清空对话历史"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id] = []
    
    def delete_conversation(self, conversation_id: str) -> None:
        """删除对话"""
        self.conversations.pop(conversation_id, None)
        self.metadata.pop(conversation_id, None)
    
    def get_conversation_list(self) -> List[Dict[str, Any]]:
        """获取所有对话列表"""
        result = []
        for conv_id, messages in self.conversations.items():
            if messages:
                last_message = messages[-1]
                result.append({
                    "conversation_id": conv_id,
                    "last_message": last_message["content"][:100],
                    "message_count": len(messages),
                    "created_at": self.metadata.get(conv_id, {}).get("created_at"),
                    "updated_at": last_message.get("timestamp"),
                })
        return result


# 全局对话管理器实例
conversation_manager = ConversationManager()
