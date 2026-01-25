"""
AI 模块自定义异常
"""


class AIError(Exception):
    """AI 模块基础异常"""
    pass


class GeminiAPIError(AIError):
    """Gemini API 调用失败"""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


class AIOutputParseError(AIError):
    """AI 输出解析失败"""
    def __init__(self, message: str, raw_output: str = None):
        super().__init__(message)
        self.raw_output = raw_output


class AIOutputValidationError(AIError):
    """AI 输出验证失败"""
    def __init__(self, message: str, errors: list = None):
        super().__init__(message)
        self.errors = errors or []


class AIRetryExhaustedError(AIError):
    """重试次数用尽"""
    def __init__(self, message: str, attempts: int, last_error: Exception = None):
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error