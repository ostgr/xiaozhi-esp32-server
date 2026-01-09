import json

TAG = __name__
EMOJI_MAP = {
    "😂": "laughing",
    "😭": "crying",
    "😠": "angry",
    "😔": "sad",
    "😍": "loving",
    "😲": "surprised",
    "😱": "shocked",
    "🤔": "thinking",
    "😌": "relaxed",
    "😴": "sleepy",
    "😜": "silly",
    "🙄": "confused",
    "😶": "neutral",
    "🙂": "happy",
    "😆": "laughing",
    "😳": "embarrassed",
    "😉": "winking",
    "😎": "cool",
    "🤤": "delicious",
    "😘": "kissy",
    "😏": "confident",
}
EMOJI_RANGES = [
    (0x1F600, 0x1F64F),
    (0x1F300, 0x1F5FF),
    (0x1F680, 0x1F6FF),
    (0x1F900, 0x1F9FF),
    (0x1FA70, 0x1FAFF),
    (0x2600, 0x26FF),
    (0x2700, 0x27BF),
]


def get_string_no_punctuation_or_emoji(s):
    """Remove leading/trailing punctuation and emoji, but preserve spaces

    Note: Spaces are preserved at all positions (leading, internal, trailing)
    because they mark word boundaries in Vietnamese and other languages.
    The original code removed ALL spaces, which broke word segmentation.
    """
    chars = list(s)
    # 处理开头的字符（只删除标点/emoji，不删除空格）
    start = 0
    while start < len(chars):
        if is_punctuation_or_emoji(chars[start]) and not chars[start].isspace():
            start += 1
        else:
            break

    # 处理结尾的字符（只删除标点/emoji，不删除空格）
    end = len(chars) - 1
    while end >= start:
        if is_punctuation_or_emoji(chars[end]) and not chars[end].isspace():
            end -= 1
        else:
            break

    result = "".join(chars[start : end + 1])
    # Then strip leading/trailing whitespace only (not internal spaces)
    return result.strip()


def is_punctuation_or_emoji(char):
    """检查字符是否为指定标点或表情符号（NOT spaces）

    Note: Spaces are NOT treated as punctuation to preserve word boundaries
    in Vietnamese and other languages that rely on spaces for word segmentation.
    """
    # 定义需要去除的中英文标点（包括全角/半角）
    punctuation_set = {
        "，",
        ",",  # 中文逗号 + 英文逗号
        "。",
        ".",  # 中文句号 + 英文句号
        "！",
        "!",  # 中文感叹号 + 英文感叹号
        """,
        """,
        '"',  # 中文双引号 + 英文引号
        "：",
        ":",  # 中文冒号 + 英文冒号
        "-",
        "－",  # 英文连字符 + 中文全角横线
        "、",  # 中文顿号
        "[",
        "]",  # 方括号
        "【",
        "】",  # 中文方括号
    }
    # NOTE: Removed char.isspace() check to preserve spaces for word boundaries
    if char in punctuation_set:
        return True
    return is_emoji(char)


async def get_emotion(conn, text):
    """获取文本内的情绪消息"""
    emoji = "🙂"
    emotion = "happy"
    for char in text:
        if char in EMOJI_MAP:
            emoji = char
            emotion = EMOJI_MAP[char]
            break
    try:
        await conn.websocket.send(
            json.dumps(
                {
                    "type": "llm",
                    "text": emoji,
                    "emotion": emotion,
                    "session_id": conn.session_id,
                }
            )
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).warning(f"发送情绪表情失败，错误:{e}")
    return


def is_emoji(char):
    """检查字符是否为emoji表情"""
    code_point = ord(char)
    return any(start <= code_point <= end for start, end in EMOJI_RANGES)


def check_emoji(text):
    """去除文本中的所有emoji表情"""
    return ''.join(char for char in text if not is_emoji(char) and char != "\n")
