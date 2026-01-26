"""
Gemini API Client

封装 Google Gemini API，提供统一的调用接口。
支持 Pro（高质量）和 Flash（高速）两种模型。
"""

import json
import asyncio
from typing import AsyncGenerator, Type, TypeVar, Literal, Optional
from pydantic import BaseModel, ValidationError

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.config import settings
from app.ai.exceptions import (
    GeminiAPIError,
    AIOutputParseError,
    AIOutputValidationError,
    AIRetryExhaustedError,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 泛型类型变量，用于 generate_structured
T = TypeVar('T', bound=BaseModel)


class GeminiClient:
    """
    Gemini API 统一客户端
    
    提供两种模型：
    - Pro: 用于主叙事生成、复杂推理（更聪明但较慢）
    - Flash: 用于 NPC 决策、批量处理（更快但略简单）
    
    使用示例：
```python
    client = GeminiClient(api_key="...")
    
    # 简单文本生成
    text = await client.generate("Tell me a story")
    
    # 结构化输出
    response = await client.generate_structured(
        prompt="...",
        response_model=GameActionResponse
    )
```
    """
    
    # 模型名称映射
    MODEL_MAP = {
        "pro": "models/gemini-pro-latest",
        "flash": "models/gemini-flash-latest",
    }
    
    # 默认配置
    DEFAULT_CONFIG = {
        "pro": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_output_tokens": 2048,
        },
        "flash": {
            "temperature": 0.5,
            "top_p": 0.85,
            "max_output_tokens": 1024,
        }
    }
    
    def __init__(self, api_key: str = None):
        """
        初始化 Gemini 客户端
        
        Args:
            api_key: Gemini API 密钥，如果不提供则从配置读取
        """
        self.api_key = api_key or settings.gemini_api_key
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # 配置 SDK
        genai.configure(api_key=self.api_key)
        
        # 初始化模型实例
        self._models = {
            "pro": genai.GenerativeModel(self.MODEL_MAP["pro"]),
            "flash": genai.GenerativeModel(self.MODEL_MAP["flash"]),
        }
        
        logger.info("GeminiClient initialized with Pro and Flash models")
    
    def _get_model(self, model: Literal["pro", "flash"]) -> genai.GenerativeModel:
        """获取指定模型实例"""
        return self._models[model]
    
    def _get_generation_config(
        self,
        model: Literal["pro", "flash"],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> GenerationConfig:
        """构建生成配置"""
        config = self.DEFAULT_CONFIG[model].copy()
        
        if temperature is not None:
            config["temperature"] = temperature
        if max_tokens is not None:
            config["max_output_tokens"] = max_tokens
            
        return GenerationConfig(**config)
    
    # ===========================================
    # 核心方法：基础文本生成
    # ===========================================
    
    async def generate(
        self,
        prompt: str,
        model: Literal["pro", "flash"] = "pro",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        基础文本生成
        
        Args:
            prompt: 用户提示词
            model: 使用的模型 ("pro" 或 "flash")
            temperature: 温度参数（可选，覆盖默认值）
            max_tokens: 最大输出 token 数（可选）
            system_instruction: 系统指令（可选）
            
        Returns:
            生成的文本
            
        Raises:
            GeminiAPIError: API 调用失败
        """
        try:
            logger.debug(f"Generating with {model}, prompt length: {len(prompt)}")
            
            # 获取模型
            gemini_model = self._get_model(model)
            
            # 如果有系统指令，创建新的模型实例
            if system_instruction:
                gemini_model = genai.GenerativeModel(
                    self.MODEL_MAP[model],
                    system_instruction=system_instruction
                )
            
            # 生成配置
            config = self._get_generation_config(model, temperature, max_tokens)
            
            # 调用 API（同步方法，但我们在异步上下文中运行）
            # 使用 asyncio.to_thread 将同步调用放到线程池
            response = await asyncio.to_thread(
                gemini_model.generate_content,
                prompt,
                generation_config=config
            )
            
            # 提取文本
            if not response.text:
                raise GeminiAPIError("Empty response from Gemini")
            
            logger.debug(f"Generated {len(response.text)} chars")
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise GeminiAPIError(f"Failed to generate: {str(e)}", original_error=e)
    
    # ===========================================
    # 核心方法：结构化输出生成
    # ===========================================
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        model: Literal["pro", "flash"] = "pro",
        temperature: Optional[float] = None,
        max_retries: int = 3,
        system_instruction: Optional[str] = None,
    ) -> T:
        """
        结构化输出生成
        
        强制 AI 返回符合指定 Pydantic 模型的 JSON。
        
        Args:
            prompt: 用户提示词
            response_model: 期望的响应 Pydantic 模型类
            model: 使用的模型
            temperature: 温度参数
            max_retries: 最大重试次数
            system_instruction: 额外的系统指令
            
        Returns:
            解析后的 Pydantic 模型实例
            
        Raises:
            AIRetryExhaustedError: 重试次数用尽
            AIOutputParseError: JSON 解析失败
            AIOutputValidationError: Schema 验证失败
        """
        # 获取 JSON Schema
        schema = response_model.model_json_schema()
        
        # 构建强制 JSON 输出的提示
        json_instruction = self._build_json_instruction(schema)
        
        # 合并系统指令
        full_system_instruction = f"""
{system_instruction or ""}

{json_instruction}
""".strip()
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Structured generation attempt {attempt + 1}/{max_retries}")
                
                # 生成响应
                raw_response = await self.generate(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    system_instruction=full_system_instruction,
                )
                
                # 清理响应（移除可能的 markdown 标记）
                cleaned = self._clean_json_response(raw_response)
                
                # 解析 JSON
                try:
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError as e:
                    raise AIOutputParseError(
                        f"Invalid JSON: {str(e)}",
                        raw_output=raw_response
                    )
                
                # 用 Pydantic 验证
                try:
                    result = response_model.model_validate(parsed)
                    logger.debug(f"Successfully parsed response on attempt {attempt + 1}")
                    return result
                except ValidationError as e:
                    raise AIOutputValidationError(
                        f"Schema validation failed: {str(e)}",
                        errors=e.errors()
                    )
                    
            except (AIOutputParseError, AIOutputValidationError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                # 如果还有重试机会，调整 prompt 或温度
                if attempt < max_retries - 1:
                    # 降低温度以获得更确定性的输出
                    temperature = max(0.1, (temperature or 0.7) - 0.2)
                    logger.debug(f"Retrying with temperature {temperature}")
                continue
                
            except GeminiAPIError:
                # API 错误直接抛出，不重试
                raise
        
        # 重试用尽
        raise AIRetryExhaustedError(
            f"Failed to generate valid structured output after {max_retries} attempts",
            attempts=max_retries,
            last_error=last_error
        )
    
    # ===========================================
    # 核心方法：流式生成
    # ===========================================
    
    async def generate_stream(
        self,
        prompt: str,
        model: Literal["pro", "flash"] = "pro",
        temperature: Optional[float] = None,
        system_instruction: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式文本生成
        
        用于实现打字机效果，逐步返回生成的文本。
        
        Args:
            prompt: 用户提示词
            model: 使用的模型
            temperature: 温度参数
            system_instruction: 系统指令
            
        Yields:
            文本片段
        """
        try:
            logger.debug(f"Starting stream generation with {model}")
            
            gemini_model = self._get_model(model)
            
            if system_instruction:
                gemini_model = genai.GenerativeModel(
                    self.MODEL_MAP[model],
                    system_instruction=system_instruction
                )
            
            config = self._get_generation_config(model, temperature)
            
            # 同步流式生成
            response = gemini_model.generate_content(
                prompt,
                generation_config=config,
                stream=True
            )
            
            # 逐块 yield
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
            logger.debug("Stream generation complete")
            
        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            raise GeminiAPIError(f"Stream failed: {str(e)}", original_error=e)
    
    # ===========================================
    # 核心方法：批量并行生成
    # ===========================================
    
    async def generate_batch(
        self,
        prompts: list[str],
        model: Literal["pro", "flash"] = "flash",
        temperature: Optional[float] = None,
        max_concurrent: int = 5,
    ) -> list[str]:
        """
        批量并行生成
        
        用于同时处理多个 NPC 的决策。
        
        Args:
            prompts: 提示词列表
            model: 使用的模型（推荐 flash）
            temperature: 温度参数
            max_concurrent: 最大并发数
            
        Returns:
            响应列表，与输入顺序一致
        """
        logger.debug(f"Batch generating {len(prompts)} prompts with {model}")
        
        # 使用信号量限制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_one(prompt: str, index: int) -> tuple[int, str]:
            async with semaphore:
                result = await self.generate(prompt, model=model, temperature=temperature)
                return index, result
        
        # 并发执行
        tasks = [
            generate_one(prompt, i) 
            for i, prompt in enumerate(prompts)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 按原始顺序排列结果
        ordered_results = [None] * len(prompts)
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                errors.append(result)
            else:
                index, text = result
                ordered_results[index] = text
        
        if errors:
            logger.warning(f"Batch generation had {len(errors)} errors")
        
        return ordered_results
    
    # ===========================================
    # 辅助方法
    # ===========================================
    
    def _build_json_instruction(self, schema: dict) -> str:
        """构建强制 JSON 输出的指令"""
        return f"""
RESPONSE FORMAT REQUIREMENT:
You MUST respond with a valid JSON object. Follow these rules strictly:

1. Output ONLY the JSON object - no other text before or after
2. Do NOT wrap the JSON in markdown code blocks (no ```)
3. Ensure all required fields are present
4. Use only the allowed values for enum fields

Required JSON Schema:
{json.dumps(schema, indent=2)}
"""
    
    def _clean_json_response(self, response: str) -> str:
        """
        清理 AI 响应，提取纯 JSON
        
        AI 有时会在 JSON 前后添加额外文本或 markdown 标记。
        """
        text = response.strip()
        
        # 移除 markdown 代码块标记
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
            
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        # 尝试找到 JSON 对象的开始和结束
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]
        
        return text


# ===========================================
# 便捷函数
# ===========================================

# 全局客户端实例（懒加载）
_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """
    获取全局 Gemini 客户端实例
    
    使用单例模式避免重复初始化。
    """
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client