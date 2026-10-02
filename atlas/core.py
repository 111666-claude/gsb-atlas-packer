"""贴图图集打包：把一批矩形贴图按行排进固定宽度的图集。

口径见 README：按 (-max(w, h), -w*h, name) 排序；四周留 padding；
行高取行内最大高度；允许时可旋转 90 度；两种朝向都放不下的计入
rejected；高度为最后一行 y + 行高 + padding；单遍放置，不做逐张
重叠遍历。
"""


class Packer:
    """按固定宽度排布贴图。"""

    def __init__(self, width, padding=1, allow_rotate=True):
        self.width = width
        self.padding = padding
        self.allow_rotate = allow_rotate
        self.overlap_checks = 0

    def pack(self, items):
        self.overlap_checks = 0
        placed = []
        rejected = 0
        pad = self.padding
        width = self.width
        x = pad
        y = pad
        row_h = 0

        ordered = sorted(items, key=lambda it: (-max(it[1], it[2]), -it[1] * it[2], it[0]))

        for name, w, h in ordered:
            orientations = [(w, h, False)]
            if self.allow_rotate and w != h:
                orientations.append((h, w, True))

            choice = None
            for ow, oh, rot in orientations:
                self.overlap_checks += 1
                if x + ow + pad <= width:
                    choice = (ow, oh, rot)
                    break
            if choice is None:
                if x == pad:
                    # 空行都放不下：两种朝向均被拒绝
                    rejected += 1
                    continue
                y += row_h + pad
                x = pad
                row_h = 0
                for ow, oh, rot in orientations:
                    self.overlap_checks += 1
                    if x + ow + pad <= width:
                        choice = (ow, oh, rot)
                        break
            if choice is None:
                rejected += 1
                continue

            ow, oh, rot = choice
            placed.append({
                "name": name,
                "x": x,
                "y": y,
                "w": ow,
                "h": oh,
                "rotated": rot,
            })
            x += ow + pad
            row_h = max(row_h, oh)

        height = y + row_h + pad if placed else 0
        area = sum(p["w"] * p["h"] for p in placed)
        coverage = 0.0 if height == 0 else area * 100.0 / (width * height)
        return {
            "width": width,
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
