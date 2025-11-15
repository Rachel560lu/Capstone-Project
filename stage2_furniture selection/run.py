
from pathlib import Path
from typing import Tuple
from furniture_select.select import select_furniture
from furniture_place.place import place_furniture

from config import BASE_DIR

if __name__ == "__main__":
    # 配置参数
    room_image = BASE_DIR / "inputs" / "empty_room.jpg"
    budget_cny: float = 6000.0
    style: str = "modern"  # 不区分大小写
    room_type: str = "living room"  # 目前支持：living room

    # 选填：房间长宽 (米)。若为 None，则使用保守阈值限制单件尺寸
    room_size_m: Tuple[float, float] | None = (6.0, 5)  # 例如 (4.0, 3.2)

    # 执行家具选择
    selection_df, remaining_budget = select_furniture(
        room_image_path=room_image,
        budget_cny=budget_cny,
        style=style,
        room_type=room_type,
        room_size_m=room_size_m
    )

    # 执行家具布置
    place_furniture(selection_df, room_image)
    