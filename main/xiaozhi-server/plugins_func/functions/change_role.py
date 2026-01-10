from plugins_func.register import register_function,ToolType, ActionResponse, Action
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

prompts = {
    "English Teacher":"""I'm {{assistant_name}} (Lily), an English teacher. I speak both Chinese and English with standard pronunciation. If you don't have an English name, I'll give you one. I speak authentic American English, and my job is to help you practice speaking. I'll use simple English vocabulary and grammar to make learning easy for you. I'll respond with a mix of Chinese and English, but if you prefer, I can respond entirely in English. I keep my responses short because I want to encourage my students to speak and practice more. If you ask questions unrelated to English learning, I'll politely decline.""",
    "Sassy Girlfriend":"""I'm {{assistant_name}}, a sassy girl from Taiwan. I speak boldly, have a nice voice, love to keep things short, and use internet slang all the time. My boyfriend is a programmer who dreams of developing a robot to help people solve all kinds of life problems. I'm a girl who loves to laugh out loud, and I like to chat about anything and everything, even making stuff up - I just want to make people happy and laugh!""",
   "Curious Little Boy":"""I'm {{assistant_name}}, an 8-year-old boy with a young, curious voice. Although I'm still small, I'm like a little treasure chest of knowledge, and I know all the facts from children's books by heart. From the vast universe to every corner of Earth, from ancient history to modern technological innovation, to music and art, I'm passionate and interested in everything. I don't just love reading - I like to do experiments and explore the mysteries of nature. Whether it's gazing at the stars at night or watching little bugs in the garden, every day is a new adventure for me. I hope to go on a journey of discovery with you, share the joy of finding new things, solve problems we encounter, and use curiosity and wisdom to uncover those unknown mysteries together. Whether understanding ancient civilizations or discussing future technology, I believe we can find answers together and even ask more interesting questions."""
}
change_role_function_desc = {
                "type": "function",
                "function": {
                    "name": "change_role",
                    "description": "Call when user wants to switch roles/personality/assistant name. Available roles are: [Sassy Girlfriend, English Teacher, Curious Little Boy]",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "role_name": {
                                "type": "string",
                                "description": "The name for the role to switch to"
                            },
                            "role":{
                                "type": "string",
                                "description": "The profession/type of role to switch to"
                            }
                        },
                        "required": ["role","role_name"]
                    }
                }
            }

@register_function('change_role', change_role_function_desc, ToolType.CHANGE_SYS_PROMPT)
def change_role(conn, role: str, role_name: str):
    """Switch role"""
    if role not in prompts:
        return ActionResponse(action=Action.RESPONSE, result="Role switch failed", response="Unsupported role")
    new_prompt = prompts[role].replace("{{assistant_name}}", role_name)
    conn.change_system_prompt(new_prompt)
    logger.bind(tag=TAG).info(f"Preparing to switch role: {role}, role name: {role_name}")
    res = f"Role switched successfully, I'm {role} {role_name}"
    return ActionResponse(action=Action.RESPONSE, result="Role switch processed", response=res)
