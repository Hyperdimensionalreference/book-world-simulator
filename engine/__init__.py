"""书中世界模拟器 —— 与具体书籍解耦的游玩引擎。

引擎只消费「世界数据包」（package），不读原文，不调用任何在线模型。
"""

from .models import WorldPackage, load_package
from .state import GameState
from .runner import GameRunner

__all__ = ["WorldPackage", "load_package", "GameState", "GameRunner"]
