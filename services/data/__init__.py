"""
数据访问层模块
提供数据访问的抽象层，实现Repository模式
"""

from .config_repository import ConfigRepository
from .game_data_repository import GameDataRepository
from .player_repository import PlayerRepository

__all__ = ['ConfigRepository', 'GameDataRepository', 'PlayerRepository']
