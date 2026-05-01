from khl.card import CardMessage, Card, Module, Types
from khl import Message


async def reply_with_card(msg: Message, text: str, title: str = "🤖 太美"):
    """将回复包装成 KOOK Card 消息发送"""
    card = Card(
        Module.Section(f"**{title}**"),
        Module.Divider(),
        Module.Section(text),
        theme=Types.Theme.INFO,
    )
    cm = CardMessage()
    cm.append(card)
    await msg.reply(cm)
