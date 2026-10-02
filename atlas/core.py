"""贴图图集打包：把一批矩形贴图排进固定宽度的图集，记录位置、朝向与溢出。

口径（与 README 一致）：按 (-max(w, h), -w*h, name) 升序做架式单遍排布；
每张贴图四周留 padding，首图左上角为 (padding, padding)；行高取该行最大
高度，下一行 y = 上一行 y + 行高 + padding；允许旋转时可转 90 度并交换
宽高、标记 rotated；两种朝向都放不下的计入 rejected，不占坐标；高度等于
最后一行 y + 行高 + padding，coverage 为已放面积除以 width * height。
"""


class Packer:
    """按固定宽度排布贴图（架式排布，每张贴图 O(1) 放置）。"""

    def __init__(self, width, padding=1, allow_rotate=True):
        self.width = width
        self.padding = padding
        self.allow_rotate = allow_rotate
        self.overlap_checks = 0

    def _fits_width(self, side):
        return side + 2 * self.padding <= self.width

    def pack(self, items):
        ordered = sorted(items, key=lambda item: (-max(item[1], item[2]),
                                                  -(item[1] * item[2]),
                                                  item[0]))
        placed = []
        rejected = 0
        pad = self.padding
        x = pad
        y = pad
        row_h = 0
        for name, w, h in ordered:
            if not self._fits_width(w) \
                    and not (self.allow_rotate and self._fits_width(h)):
                rejected += 1
                continue
            self.overlap_checks += 1
            rotated = False
            if x + w + pad > self.width:
                if self.allow_rotate and w != h \
                        and x + h + pad <= self.width:
                    w, h = h, w
                    rotated = True
                else:
                    y += row_h + pad
                    x = pad
                    row_h = 0
                    if not self._fits_width(w):
                        w, h = h, w
                        rotated = True
            placed.append({
                "name": name,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "rotated": rotated,
            })
            x += w + pad
            if h > row_h:
                row_h = h
        height = 0 if not placed else y + row_h + pad
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
