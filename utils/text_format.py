import re


def sanitize_kook_text(text: str) -> str:
    """过滤文本，只保留 KOOK 支持的格式"""
    allowed_blocks = []
    for block in text.split('\n'):
        stripped = block.strip()

        if stripped.startswith('|') and stripped.endswith('|'):
            continue

        if re.match(r'^#{1,6}\s', stripped):
            allowed_blocks.append(stripped.lstrip('#').strip())
            continue

        if re.match(r'^[*-]{3,}$', stripped):
            continue

        if re.match(r'^>\s', stripped):
            allowed_blocks.append(stripped[1:].strip())
            continue

        allowed_blocks.append(block)

    text = '\n'.join(allowed_blocks)

    text = re.sub(r'^(\s*[-*+]\s)', r'\1', text, flags=re.MULTILINE)

    return text.strip()
