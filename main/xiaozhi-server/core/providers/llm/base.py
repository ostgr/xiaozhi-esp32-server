from abc import ABC, abstractmethod
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

class LLMProviderBase(ABC):
    @abstractmethod
    def response(self, session_id, dialogue):
        """LLM response generator"""
        pass

    def response_no_stream(self, system_prompt, user_prompt, **kwargs):
        try:
            # 构造对话格式
            dialogue = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            logger.bind(tag=TAG).info(
                f"[LLM STREAMING] Starting LLM response (no_stream mode)"
            )
            logger.bind(tag=TAG).debug(
                f"[LLM STREAMING] System prompt ({len(system_prompt)} chars): {system_prompt[:80]}..."
            )
            logger.bind(tag=TAG).debug(
                f"[LLM STREAMING] User prompt: {user_prompt[:100]}..."
            )

            result = ""
            token_count = 0
            for part in self.response("", dialogue, **kwargs):
                result += part
                token_count += 1
                if token_count % 10 == 0:
                    logger.bind(tag=TAG).debug(
                        f"[LLM STREAMING] Received {token_count} tokens, accumulated: {len(result)} chars"
                    )

            logger.bind(tag=TAG).info(
                f"[LLM STREAMING] Completed LLM response (tokens={token_count}, length={len(result)}, text={result[:80]}...)"
            )
            return result

        except Exception as e:
            logger.bind(tag=TAG).error(f"[LLM STREAMING] Error in LLM response generation: {e}")
            return "【LLM服务响应异常】"
    
    def response_with_functions(self, session_id, dialogue, functions=None):
        """
        Default implementation for function calling (streaming)
        This should be overridden by providers that support function calls

        Returns: generator that yields either text tokens or a special function call token
        """
        logger.bind(tag=TAG).info(
            f"[LLM STREAMING] Starting LLM response with functions (session={session_id[:8]}...)"
        )
        logger.bind(tag=TAG).debug(
            f"[LLM STREAMING] Dialogue has {len(dialogue)} messages"
        )
        if functions:
            logger.bind(tag=TAG).debug(
                f"[LLM STREAMING] Available functions: {[f.get('name', 'unknown') for f in functions]}"
            )

        token_count = 0
        # For providers that don't support functions, just return regular response
        for token in self.response(session_id, dialogue):
            token_count += 1
            if token_count % 20 == 0:
                logger.bind(tag=TAG).debug(
                    f"[LLM STREAMING] Received {token_count} tokens with functions"
                )
            yield token, None

        logger.bind(tag=TAG).info(
            f"[LLM STREAMING] Completed LLM response with functions (tokens={token_count})"
        )

