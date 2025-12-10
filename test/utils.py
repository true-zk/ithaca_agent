from datetime import datetime
import json
from pathlib import Path


def save_conversation(messages, filename: str = None):
    """简洁函数：将完整的messages对象保存为可读JSON"""
    if filename is None:
        filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 转换messages为可序列化格式
    serialized_messages = []
    for msg in messages:
        msg_dict = {
            "role": msg.type,  # "human", "ai", "tool"
            "content": msg.content,
            "id": msg.id if hasattr(msg, 'id') else None,
            "timestamp": msg.response_metadata.get('timestamp') if hasattr(msg, 'response_metadata') else None
        }
        serialized_messages.append(msg_dict)
    
    # 保存为JSON
    output = {
        "timestamp": datetime.now().isoformat(),
        "message_count": len(messages),
        "messages": serialized_messages
    }
    
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 已保存到: {filename}")
    return filename