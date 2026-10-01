"""命令行入口：跑图集打包样例。"""

import argparse

from .core import Packer, out_of_bounds, overlapping


def build_parser():
    parser = argparse.ArgumentParser(prog="atlas-packer", description="贴图图集打包")
    parser.add_argument("--sample", default="pack",
                        help="pack / rotate / padding / too_wide / coverage / scale")
    return parser


PACK_ITEMS = [("hero", 40, 30), ("potion", 24, 24), ("coin", 20, 20), ("sword", 32, 16)]


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "pack":
        result = Packer(64, padding=2).pack(PACK_ITEMS)
        print("height=%d overlap=%d coverage=%.1f"
              % (result["height"], overlapping(result), result["coverage"]))
    elif args.sample == "rotate":
        result = Packer(40, padding=2).pack([("banner", 44, 30)])
        rotated = sum(1 for p in result["placed"] if p["rotated"])
        print("rotated=%d out_of_bounds=%d" % (rotated, out_of_bounds(result)))
    elif args.sample == "padding":
        result = Packer(64, padding=2).pack([("a", 18, 18), ("b", 18, 18), ("c", 18, 18)])
        rects = sorted(result["placed"], key=lambda p: p["x"])
        gaps = [rects[i + 1]["x"] - (rects[i]["x"] + rects[i]["w"])
                for i in range(len(rects) - 1)]
        print("min_gap=%d" % (min(gaps) if gaps else 0))
    elif args.sample == "too_wide":
        result = Packer(64, padding=2).pack([("sky", 80, 70), ("tile", 20, 20)])
        print("rejected=%d out_of_bounds=%d"
              % (result["rejected"], out_of_bounds(result)))
    elif args.sample == "coverage":
        result = Packer(64, padding=2).pack([("a", 30, 30), ("b", 30, 30)])
        print("coverage=%.1f" % result["coverage"])
    elif args.sample == "scale":
        items = [("t-%d" % i, 8 + (i % 5), 8 + (i % 3)) for i in range(5000)]
        result = Packer(256, padding=1).pack(items)
        print("overlap_checks=%d" % result["overlap_checks"])
    else:
        raise SystemExit("需要 --sample pack|rotate|padding|too_wide|coverage|scale")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
