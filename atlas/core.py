"""贴图图集打包：把一批矩形贴图排进固定宽度的图集，记录位置、朝向与溢出。

缺陷：不排序、行高只记最后一项、忽略边距、超宽不拒绝、覆盖率按行高算错、
每次放置都遍历已放贴图做重叠检查。
"""


class Packer:
    """按固定宽度排布贴图。"""

    def __init__(self, width, padding=1, allow_rotate=True):
        self.width = width
        self.padding = padding
        self.allow_rotate = allow_rotate
        self.overlap_checks = 0

    def pack(self, items):
        placed = []
        rejected = 0
        x = 0
        y = 0
        row_h = 0
        for name, w, h in items:
            self.overlap_checks += len(placed)
            rotated = False
            if self.allow_rotate and w > h and x + h > self.width:
                w, h = h, w
                rotated = True
            if x + w > self.width:
                y += row_h
                x = 0
                row_h = 0
            placed.append({
                "name": name,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "rotated": rotated,
            })
            x += w
            row_h = h
        height = y + row_h
        area = sum(p["w"] * p["h"] for p in placed)
        coverage = 0.0 if height == 0 else area * 100.0 / (self.width * height)
        return {
            "width": self.width,
            "height": height,
            "placed": placed,
            "rejected": rejected,
            "coverage": coverage,
            "overlap_checks": self.overlap_checks,
        }


def overlapping(result):
    """统计互相重叠的贴图对数（只给样例核对用）。"""
    rects = result["placed"]
    count = 0
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a = rects[i]
            b = rects[j]
            if a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] \
                    and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]:
                count += 1
    return count


def out_of_bounds(result):
    """统计越出图集左右边界或压在负坐标上的贴图数（只给样例核对用）。"""
    count = 0
    for p in result["placed"]:
        if p["x"] < 0 or p["x"] + p["w"] > result["width"]:
            count += 1
    return count
