# atlas-packer

贴图图集打包：把一批矩形贴图排进固定宽度的图集，输出每张贴图的位置、朝向、
拒绝数量与覆盖率。只用 Python 标准库。

```
python3 -m atlas.cli --sample pack
python3 -m atlas.cli --sample rotate
python3 -m atlas.cli --sample padding
python3 -m atlas.cli --sample too_wide
python3 -m atlas.cli --sample coverage
python3 -m atlas.cli --sample scale
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **排序**：按 `(-max(w, h), -w*h, name)` 升序放置，大贴图先放。
- **边距**：每张贴图四周留 `padding`；第一张的左上角是 `(padding, padding)`，
  同一行相邻两张之间至少 `padding`，行与行之间至少 `padding`。
- **行高**：一行的行高是该行内所有贴图高度的最大值；下一行的 `y` 等于
  上一行 `y + 行高 + padding`。
- **旋转**：`allow_rotate` 为真时，贴图可以用 90 度朝向放置，放置后 `w/h`
  必须互换并标记 `rotated`；不允许旋转时永远不标记。
- **拒绝**：`min(w, h) + 2*padding > width` 的贴图两种朝向都放不下，计入
  `rejected`，不占坐标；其余贴图必须完整落在 `[0, width)` 之内。
- **高度与覆盖率**：图集高度等于最后一行 `y + 行高 + padding`；
  `coverage` 是已放贴图面积之和除以 `width * height` 的百分比。
- **查询代价**：放置过程不许逐张遍历已放贴图求重叠，`overlap_checks`
  不随已放数量线性增长。
- **规模**：1 万张贴图单遍排完，内存 O(已放贴图数)。
- **确定性**：同一批贴图重复打包，位置、朝向、高度与覆盖率完全一致。

## 输出契约（不改格式）

```
height=.. overlap=.. coverage=..
rotated=.. out_of_bounds=..
min_gap=..
rejected=.. out_of_bounds=..
coverage=..
overlap_checks=..
```

## 目录

```
atlas/core.py   排布、朝向、拒绝与覆盖率
atlas/cli.py    命令行入口
tests/          unittest 用例
```
