"""
Validator Base Classes

验证器基类和通用工具。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum


class ValidationSeverity(str, Enum):
    """验证问题严重程度"""
    ERROR = "error"       # 致命错误，必须处理
    WARNING = "warning"   # 警告，可以继续但需注意
    INFO = "info"         # 信息，仅供参考


@dataclass
class ValidationIssue:
    """单个验证问题"""
    code: str                           # 问题代码
    message: str                        # 人类可读的描述
    severity: ValidationSeverity        # 严重程度
    field: Optional[str] = None         # 相关字段
    value: Optional[Any] = None         # 问题值
    suggestion: Optional[str] = None    # 修复建议


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool                                     # 是否通过验证
    issues: List[ValidationIssue] = field(default_factory=list)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """获取所有错误"""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """获取所有警告"""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
    
    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0
    
    def add_error(self, code: str, message: str, **kwargs):
        """添加错误"""
        self.issues.append(ValidationIssue(
            code=code,
            message=message,
            severity=ValidationSeverity.ERROR,
            **kwargs
        ))
        self.valid = False
    
    def add_warning(self, code: str, message: str, **kwargs):
        """添加警告"""
        self.issues.append(ValidationIssue(
            code=code,
            message=message,
            severity=ValidationSeverity.WARNING,
            **kwargs
        ))
    
    def merge(self, other: 'ValidationResult'):
        """合并另一个验证结果"""
        self.issues.extend(other.issues)
        if not other.valid:
            self.valid = False


class BaseValidator(ABC):
    """验证器基类"""
    
    @abstractmethod
    def validate(self, *args, **kwargs) -> ValidationResult:
        """执行验证"""
        pass