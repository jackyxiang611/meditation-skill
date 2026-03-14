#!/usr/bin/env python3
"""Generate a line-by-line meditation script with PAUSE/BOWL markers.

Output format (one item per line):
- Normal sentence (TTS per line)
- [[PAUSE:seconds]]
- [[BOWL]]

This is a pragmatic generator for demos; you can replace rules later.

Usage:
  python3 scripts/generate_script.py --out tmp/script.txt --goal 减压 --minutes 5 --name Jacky
"""

import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--goal", default="减压")
    ap.add_argument("--minutes", type=int, default=5)
    ap.add_argument("--name", default="")
    args = ap.parse_args()

    name = args.name.strip()
    who = f"{name}，" if name else ""

    # A simple script: intentionally MORE pauses for user actions (breathing / scanning / bowl).
    lines = []

    # goal-specific opening tone
    if args.goal == "助眠":
        opening = [
            f"{who}晚安。欢迎你来到这段准备入睡的时间。",
            "接下来这几分钟，你不需要再努力。",
            "你只需要让自己慢慢安静下来。",
        ]
    else:
        opening = [
            f"{who}嗨。欢迎你来到这段属于自己的时间。",
            "现在的这几分钟，你不需要解决任何问题。",
            "你只需要把注意力带回到自己。",
        ]

    lines += [
        *opening,
        "[[PAUSE:4]]",
        "先找一个舒服的姿势。躺下会更适合入睡，当然坐着也可以。",
        "让眼皮变得沉一点，视线柔和一点。",
        "[[PAUSE:6]]",

        "我们从呼吸开始。",
        "慢慢吸气……",
        "[[PAUSE:4]]",
        "缓缓呼气……",
        "[[PAUSE:6]]",

        "再来两轮。",
        "吸气……",
        "[[PAUSE:3]]",
        "呼气……",
        "[[PAUSE:4]]",
        "吸气……",
        "[[PAUSE:3]]",
        "呼气……",
        "[[PAUSE:4]]",

        "如果脑海里出现工作、对话、评审的画面，先不要跟着它走。",
        "你可以在心里轻轻说一句：我看见了。",
        "然后，把注意力带回呼气。",
        "[[PAUSE:5]]",

        "现在，把注意力移到肩颈。",
        "允许肩膀一点点下沉。",
        "[[PAUSE:4]]",
        "允许下巴松开。",
        "[[PAUSE:3]]",
        "允许眉心放松。",
        "[[PAUSE:4]]",

        "把注意力放到胸口。感受每一次起伏。",
        "[[PAUSE:5]]",
        "把注意力放到腹部。让呼吸更柔软一点。",
        "[[PAUSE:5]]",

        "接下来，我们做一个简短的身体扫描。",
        "从头顶开始，放松头皮。",
        "[[PAUSE:4]]",
        "放松额头。",
        "[[PAUSE:4]]",
        "放松眼周。",
        "[[PAUSE:5]]",
        "把注意力移到喉咙。想象那里有更多空间。",
        "[[PAUSE:5]]",
        "把注意力移到肩膀、上臂、前臂、手掌。",
        "感受手心的温度。感受指尖。",
        "[[PAUSE:6]]",

        "如果你愿意，想象你站在一条缓慢流动的河边。",
        "水声很轻，带走多余的念头。",
        "[[PAUSE:5]]",
        "每一次呼气，都像把压力交给河流。",
        "[[PAUSE:4]]",
        "每一次吸气，都像把新的空间带回来。",
        "[[PAUSE:5]]",

        "现在，我会敲响送钵。",
        "[[BOWL]]",
        "[[PAUSE:6]]",

        "当声音慢慢远去，把注意力带回呼吸。",
        "你可以对自己说：此刻，我允许自己休息。",
        "[[PAUSE:6]]",

        "最后，再做三次呼吸。",
        "吸气……",
        "[[PAUSE:3]]",
        "呼气……",
        "[[PAUSE:4]]",
        "吸气……",
        "[[PAUSE:3]]",
        "呼气……",
        "[[PAUSE:4]]",
        "吸气……",
        "[[PAUSE:3]]",
        "呼气……",
        "[[PAUSE:5]]",

        "当你准备好，轻轻活动手指和脚趾。",
        "感受身体与地面的接触。",
        "然后慢慢睁开眼睛。",
        "[[PAUSE:3]]",
        f"谢谢你{name or ''}。你已经做得很好了。".replace("谢谢你。", "谢谢你。"),
    ]

    with open(args.out, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln.rstrip() + "\n")


if __name__ == "__main__":
    main()
