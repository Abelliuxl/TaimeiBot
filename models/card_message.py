from typing import List, Dict, Any, Optional

class CardMessage:
    """卡片消息模型"""
    
    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content
        self.fields: List[Dict[str, str]] = []
        
    def add_field(self, name: str, value: str):
        """添加字段"""
        self.fields.append({
            "name": name,
            "value": value
        })
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "type": "card",
            "theme": "secondary",
            "size": "lg",
            "modules": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain-text",
                        "content": self.title
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "kmarkdown",
                        "content": self.content
                    }
                },
                *[{
                    "type": "section",
                    "text": {
                        "type": "kmarkdown",
                        "content": f"**{field['name']}**\n{field['value']}"
                    }
                } for field in self.fields]
            ]
        } 