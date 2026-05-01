"""
输入验证器
提供统一的输入验证功能，支持各种验证规则和错误消息
"""

import re
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from enum import Enum
from utils.logging_utils import get_logger
from utils.error_handler import ValidationError, log_error
from config.constants import SUPPORTED_REGIONS, SUPPORTED_CLASSES

logger = get_logger(__name__)

class ValidationRule(Enum):
    """验证规则枚举"""
    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    REGEX = "regex"
    EMAIL = "email"
    URL = "url"
    ALPHA = "alpha"
    ALPHANUMERIC = "alphanumeric"
    NUMERIC = "numeric"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    CUSTOM = "custom"

class ValidationResult:
    """验证结果类"""
    
    def __init__(self, is_valid: bool, error_message: Optional[str] = None):
        """
        初始化验证结果
        
        Args:
            is_valid: 是否验证通过
            error_message: 错误消息
        """
        self.is_valid = is_valid
        self.error_message = error_message
    
    def __bool__(self) -> bool:
        """布尔值转换"""
        return self.is_valid

class InputValidator:
    """输入验证器"""
    
    def __init__(self):
        """初始化输入验证器"""
        self._rules: Dict[str, List[Tuple[ValidationRule, Any, str]]] = {}
        self._custom_validators: Dict[str, Callable] = {}
        logger.info("输入验证器初始化完成")
    
    def add_rule(self, field: str, rule: ValidationRule, value: Any, error_message: str) -> 'InputValidator':
        """
        添加验证规则
        
        Args:
            field: 字段名
            rule: 验证规则
            value: 验证值
            error_message: 错误消息
            
        Returns:
            验证器实例（支持链式调用）
        """
        if field not in self._rules:
            self._rules[field] = []
        
        self._rules[field].append((rule, value, error_message))
        return self
    
    def add_custom_validator(self, name: str, validator: Callable) -> 'InputValidator':
        """
        添加自定义验证器
        
        Args:
            name: 验证器名称
            validator: 验证函数
            
        Returns:
            验证器实例（支持链式调用）
        """
        self._custom_validators[name] = validator
        return self
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """
        验证输入数据
        
        Args:
            data: 输入数据
            
        Returns:
            (是否验证通过, 错误消息字典)
        """
        errors = {}
        
        for field, rules in self._rules.items():
            field_value = data.get(field)
            
            for rule, rule_value, error_message in rules:
                try:
                    result = self._validate_field(field_value, rule, rule_value)
                    if not result.is_valid:
                        errors[field] = result.error_message or error_message
                        break  # 一个字段只要有一个验证失败就停止
                except Exception as e:
                    log_error(logger, e, {'function': 'validate', 'field': field, 'rule': rule.value})
                    errors[field] = f"验证过程中发生错误: {str(e)}"
                    break
        
        return len(errors) == 0, errors
    
    async def validate_async(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """
        异步验证输入数据
        
        Args:
            data: 输入数据
            
        Returns:
            (是否验证通过, 错误消息字典)
        """
        errors = {}
        
        for field, rules in self._rules.items():
            field_value = data.get(field)
            
            for rule, rule_value, error_message in rules:
                try:
                    result = await self._validate_field_async(field_value, rule, rule_value)
                    if not result.is_valid:
                        errors[field] = result.error_message or error_message
                        break
                except Exception as e:
                    log_error(logger, e, {'function': 'validate_async', 'field': field, 'rule': rule.value})
                    errors[field] = f"验证过程中发生错误: {str(e)}"
                    break
        
        return len(errors) == 0, errors
    
    def _validate_field(self, value: Any, rule: ValidationRule, rule_value: Any) -> ValidationResult:
        """验证单个字段"""
        if rule == ValidationRule.REQUIRED:
            if value is None or value == "":
                return ValidationResult(False, f"此字段为必填项")
        
        elif rule == ValidationRule.MIN_LENGTH:
            if value is not None and len(str(value)) < rule_value:
                return ValidationResult(False, f"长度不能少于 {rule_value} 个字符")
        
        elif rule == ValidationRule.MAX_LENGTH:
            if value is not None and len(str(value)) > rule_value:
                return ValidationResult(False, f"长度不能超过 {rule_value} 个字符")
        
        elif rule == ValidationRule.MIN_VALUE:
            if value is not None and float(value) < rule_value:
                return ValidationResult(False, f"值不能小于 {rule_value}")
        
        elif rule == ValidationRule.MAX_VALUE:
            if value is not None and float(value) > rule_value:
                return ValidationResult(False, f"值不能大于 {rule_value}")
        
        elif rule == ValidationRule.REGEX:
            if value is not None and not re.match(rule_value, str(value)):
                return ValidationResult(False, f"格式不正确")
        
        elif rule == ValidationRule.EMAIL:
            if value is not None:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, str(value)):
                    return ValidationResult(False, f"请输入有效的邮箱地址")
        
        elif rule == ValidationRule.URL:
            if value is not None:
                url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
                if not re.match(url_pattern, str(value)):
                    return ValidationResult(False, f"请输入有效的URL地址")
        
        elif rule == ValidationRule.ALPHA:
            if value is not None and not str(value).isalpha():
                return ValidationResult(False, f"只能包含字母")
        
        elif rule == ValidationRule.ALPHANUMERIC:
            if value is not None and not str(value).isalnum():
                return ValidationResult(False, f"只能包含字母和数字")
        
        elif rule == ValidationRule.NUMERIC:
            if value is not None and not str(value).isdigit():
                return ValidationResult(False, f"只能包含数字")
        
        elif rule == ValidationRule.INTEGER:
            if value is not None:
                try:
                    int(value)
                except ValueError:
                    return ValidationResult(False, f"请输入有效的整数")
        
        elif rule == ValidationRule.FLOAT:
            if value is not None:
                try:
                    float(value)
                except ValueError:
                    return ValidationResult(False, f"请输入有效的数字")
        
        elif rule == ValidationRule.BOOLEAN:
            if value is not None and str(value).lower() not in ['true', 'false', '1', '0', 'yes', 'no', 'y', 'n']:
                return ValidationResult(False, f"请输入有效的布尔值")
        
        elif rule == ValidationRule.IN_LIST:
            if value is not None and value not in rule_value:
                return ValidationResult(False, f"值必须在以下列表中: {', '.join(map(str, rule_value))}")
        
        elif rule == ValidationRule.NOT_IN_LIST:
            if value is not None and value in rule_value:
                return ValidationResult(False, f"值不能在以下列表中: {', '.join(map(str, rule_value))}")
        
        elif rule == ValidationRule.CUSTOM:
            if rule_value in self._custom_validators:
                custom_result = self._custom_validators[rule_value](value)
                if isinstance(custom_result, ValidationResult):
                    return custom_result
                elif not custom_result:
                    return ValidationResult(False, f"自定义验证失败")
        
        return ValidationResult(True)
    
    async def _validate_field_async(self, value: Any, rule: ValidationRule, rule_value: Any) -> ValidationResult:
        """异步验证单个字段"""
        if rule == ValidationRule.CUSTOM and rule_value in self._custom_validators:
            custom_result = self._custom_validators[rule_value](value)
            if asyncio.iscoroutine(custom_result):
                custom_result = await custom_result
            
            if isinstance(custom_result, ValidationResult):
                return custom_result
            elif not custom_result:
                return ValidationResult(False, f"自定义验证失败")
        
        # 对于非异步规则，使用同步验证
        return self._validate_field(value, rule, rule_value)

# 预定义的验证器
def create_command_validator() -> InputValidator:
    """创建命令验证器"""
    validator = InputValidator()
    
    # 验证命令格式
    def validate_command_format(value: str) -> ValidationResult:
        if not value or not value.startswith('/'):
            return ValidationResult(False, "命令必须以/开头")
        
        # 检查是否为已知的命令
        command_parts = value[1:].split()
        if command_parts:
            command = command_parts[0].lower()
            known_commands = ['tf', 'ai', 'help', 'ping', 'send', 'dm']
            if command not in known_commands:
                return ValidationResult(False, f"未知命令: {command_parts[0]}")
        
        return ValidationResult(True)
    
    validator.add_custom_validator('command_format', validate_command_format)
    validator.add_rule('command', ValidationRule.REQUIRED, None, "命令不能为空")
    validator.add_rule('command', ValidationRule.CUSTOM, 'command_format', "命令格式不正确")
    
    return validator

def create_talent_query_validator() -> InputValidator:
    """创建天赋查询验证器"""
    validator = InputValidator()
    
    # 验证职业专精简称
    def validate_spec_abbreviation(value: str) -> ValidationResult:
        if not value or len(value) != 3:
            return ValidationResult(False, "职业专精简称必须是3个字符")
        
        # 检查是否为支持的职业专精
        valid_specs = []
        for class_name, specs in SUPPORTED_CLASSES.items():
            for spec_name, abbrev in specs.items():
                valid_specs.append(abbrev)
        
        if value.upper() not in valid_specs:
            return ValidationResult(False, f"不支持的职业专精: {value}")
        
        return ValidationResult(True)
    
    validator.add_custom_validator('spec_abbreviation', validate_spec_abbreviation)
    validator.add_rule('spec', ValidationRule.REQUIRED, None, "职业专精不能为空")
    validator.add_rule('spec', ValidationRule.CUSTOM, 'spec_abbreviation', "职业专精格式不正确")
    
    # 验证服务器名称（可选）
    validator.add_rule('server', ValidationRule.MAX_LENGTH, 50, "服务器名称过长")
    
    # 验证区域（可选）
    validator.add_rule('region', ValidationRule.IN_LIST, SUPPORTED_REGIONS, f"不支持的区域，支持的区域: {', '.join(SUPPORTED_REGIONS)}")
    
    return validator

def create_ai_chat_validator() -> InputValidator:
    """创建AI聊天验证器"""
    validator = InputValidator()
    
    # 验证聊天内容
    validator.add_rule('message', ValidationRule.REQUIRED, None, "聊天内容不能为空")
    validator.add_rule('message', ValidationRule.MIN_LENGTH, 1, "聊天内容不能为空")
    validator.add_rule('message', ValidationRule.MAX_LENGTH, 4000, "聊天内容过长")
    
    return validator

def create_user_input_validator() -> InputValidator:
    """创建用户输入验证器"""
    validator = InputValidator()
    
    # 通用输入验证
    validator.add_rule('input', ValidationRule.REQUIRED, None, "输入内容不能为空")
    validator.add_rule('input', ValidationRule.MIN_LENGTH, 1, "输入内容不能为空")
    validator.add_rule('input', ValidationRule.MAX_LENGTH, 5000, "输入内容过长")
    
    # 敏感词过滤
    def validate_sensitive_content(value: str) -> ValidationResult:
        sensitive_words = ['垃圾', '诈骗', '色情', '暴力', '违法']
        value_lower = value.lower()
        for word in sensitive_words:
            if word in value_lower:
                return ValidationResult(False, "输入内容包含敏感词汇")
        return ValidationResult(True)
    
    validator.add_custom_validator('sensitive_content', validate_sensitive_content)
    validator.add_rule('input', ValidationRule.CUSTOM, 'sensitive_content', "输入内容包含不当词汇")
    
    return validator

# 全局验证器实例
_command_validator: Optional[InputValidator] = None
_talent_query_validator: Optional[InputValidator] = None
_ai_chat_validator: Optional[InputValidator] = None
_user_input_validator: Optional[InputValidator] = None

def get_command_validator() -> InputValidator:
    """获取命令验证器"""
    global _command_validator
    if _command_validator is None:
        _command_validator = create_command_validator()
    return _command_validator

def get_talent_query_validator() -> InputValidator:
    """获取天赋查询验证器"""
    global _talent_query_validator
    if _talent_query_validator is None:
        _talent_query_validator = create_talent_query_validator()
    return _talent_query_validator

def get_ai_chat_validator() -> InputValidator:
    """获取AI聊天验证器"""
    global _ai_chat_validator
    if _ai_chat_validator is None:
        _ai_chat_validator = create_ai_chat_validator()
    return _ai_chat_validator

def get_user_input_validator() -> InputValidator:
    """获取用户输入验证器"""
    global _user_input_validator
    if _user_input_validator is None:
        _user_input_validator = create_user_input_validator()
    return _user_input_validator

# 便捷的验证函数
async def validate_command(command: str) -> Tuple[bool, str]:
    """验证命令"""
    validator = get_command_validator()
    is_valid, errors = await validator.validate_async({'command': command})
    error_msg = errors.get('command', '') if errors else ''
    return is_valid, error_msg

async def validate_talent_query(spec: str, server: Optional[str] = None, region: Optional[str] = None) -> Tuple[bool, str]:
    """验证天赋查询"""
    data = {'spec': spec}
    if server:
        data['server'] = server
    if region:
        data['region'] = region
    
    validator = get_talent_query_validator()
    is_valid, errors = await validator.validate_async(data)
    
    # 返回第一个错误
    error_msg = next(iter(errors.values()), '') if errors else ''
    return is_valid, error_msg

async def validate_ai_chat(message: str) -> Tuple[bool, str]:
    """验证AI聊天"""
    validator = get_ai_chat_validator()
    is_valid, errors = await validator.validate_async({'message': message})
    
    # 返回第一个错误
    error_msg = errors.get('message', '') if errors else ''
    return is_valid, error_msg

async def validate_user_input(input_text: str) -> Tuple[bool, str]:
    """验证用户输入"""
    validator = get_user_input_validator()
    is_valid, errors = await validator.validate_async({'input': input_text})
    
    # 返回第一个错误
    error_msg = errors.get('input', '') if errors else ''
    return is_valid, error_msg
