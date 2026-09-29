# -*- coding: utf-8 -*-
"""数值重平：经济曲线、衰减、结局条件。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "data" / "samples" / "xinghuagou" / "package"

# ---- scenes: 修坏字段、调数值 ----
sp = PKG / "scenes.json"
scenes = json.loads(sp.read_text(encoding="utf-8"))


def find(scene_id, choice_id=None):
    for s in scenes:
        if s["id"] != scene_id:
            continue
        if choice_id is None:
            return s
        for c in s.get("choices") or []:
            if c["id"] == choice_id:
                return c
    return None


# 修 stats_note
c = find("s_linzi_borrow", "c_lend_half_linzi")
if c:
    for h in c.get("hooks") or []:
        h.pop("stats_note", None)
        if h.get("type") == "message":
            h.setdefault("stats", {})["money"] = 60

# 经济：打工/手艺类收入略提，面子消费更分明
tweaks = [
    ("s_uncle_debt", "c_ask_uncle_for_work", {"money": 50}),
    ("s_field_or_shop", "c_field_work", {"grain": 2, "money": 25}),
    ("s_field_or_shop", "c_shop_listen", {"money": -15}),
    ("s_zhao_pre_wedding", "c_face_gift", {"money": -70, "face": 7}),
    ("s_zhao_pre_wedding", "c_modest_gift", {"money": -25, "face": -1}),
    ("s_li_bedside_choice", "c_send_medicine_leave", {"money": -45}),
    ("s_bride_negotiation", "c_pay_bride_full", {"money": -260, "face": 12, "favor_in": 3}),
    ("s_bride_negotiation", "c_negotiate_bride", {"money": -110, "face": -2, "guts": 6}),
    ("s_li_death_funeral", "c_funeral_full", {"money": -45, "face": 7, "warmth": 8}),
    ("s_li_death_funeral", "c_funeral_modest", {"money": -18}),
    ("s_li_death_funeral", "c_funeral_cheap", {"money": -8, "face": -6}),
    ("s_year_end_settlement", "c_settle_debts_hard", {"money": -130, "favor_in": -3, "face": 8}),
    ("s_year_end_settlement", "c_settle_partial", {"money": -55, "favor_in": -1}),
]
for sid, cid, stat_patch in tweaks:
    ch = find(sid, cid)
    if not ch:
        print("missing", sid, cid)
        continue
    ch.setdefault("effects", {}).setdefault("stats", {}).update(stat_patch)

# 中期小额收入场景：若已有则跳过
if not find("s_odd_jobs"):
    scenes.append(
        {
            "id": "s_odd_jobs",
            "title": "零碎活",
            "turn": 6,
            "place": "village",
            "npcs": ["wang_shen"],
            "trigger": {"type": "window", "start": 6, "end": 12},
            "narration": "秋忙过了，零碎活出来了：帮人写红白帖、扛包、修院墙、抄名单。\n\n王婶在村口派活：「就看你舍不舍得下脸。」\n\n脸和钱，总有一个要弯。",
            "choices": [
                {
                    "id": "c_odd_hand",
                    "text": "出力气的活：扛包、修墙。",
                    "immediate": "你扛了一天包，肩上火辣辣的。\n\n钱到手了，是热的。\n\n有人笑：「马家小子下苦力。」也有人点头：「肯干。」",
                    "effects": {
                        "stats": {"money": 55, "health": -7, "guts": 4, "face": -2},
                        "add_memory": ["你接了出力气的零活"],
                        "add_note": "力气换钱，干净",
                    },
                    "hooks": [
                        {
                            "delay": 2,
                            "type": "message",
                            "text": "你比别人多一分体魄，白事忙起来撑得住。",
                            "stats": {"health": 3},
                        }
                    ],
                    "tags": ["挣钱", "力气"],
                },
                {
                    "id": "c_odd_craft",
                    "text": "用手艺：写帖、抄名单、算账。",
                    "requirements": {"stats": {"craft": {"min": 40}}},
                    "immediate": "你写得工整，算得清楚。\n\n主家多给了两包烟，你说不要，人家硬塞。\n\n「识字人，」他们说，「就是不一样。」",
                    "effects": {
                        "stats": {"money": 45, "craft": 4, "face": 5, "health": -2},
                        "add_memory": ["你用手艺接了零活"],
                        "add_note": "字和数也是力气",
                    },
                    "hooks": [
                        {
                            "delay": 3,
                            "type": "message",
                            "text": "后来有人专找你写东西。手艺名声是这样长起来的。",
                            "stats": {"face": 3, "craft": 3, "money": 20},
                            "actor": "village",
                        }
                    ],
                    "tags": ["挣钱", "手艺"],
                },
                {
                    "id": "c_odd_skip",
                    "text": "不接。要留着精力顾家里。",
                    "immediate": "你摇摇头走了。\n\n王婶啧了一声：「有活都不干，想啥呢。」\n\n你不是不想挣。你是怕自己顾不过来。",
                    "effects": {"stats": {"warmth": 2, "guts": -1}, "add_memory": ["你推掉了零活"], "add_note": "你把精力留给了家"},
                    "hooks": [],
                    "tags": ["顾家"],
                },
            ],
        }
    )

sp.write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- endings: 更细条件 + 新结局 ----
ep = PKG / "endings.json"
endings = json.loads(ep.read_text(encoding="utf-8"))
ids = {e["id"] for e in endings}

# 微调现有结局条件，避免「一键全中」
for e in endings:
    if e["id"] == "end_li_family":
        e["conditions"] = {
            "flags_true": ["tended_li_bedside"],
            "rel_min": {"li_jianguo": 45},
            "stats_min": {"warmth": 55},
        }
    if e["id"] == "end_face_keeper":
        e["conditions"] = {"stats_min": {"face": 78}}
    if e["id"] == "end_debt_honest":
        e["conditions"] = {"flags_true": ["settled_debts"], "stats_min": {"guts": 55}}
    if e["id"] == "end_warm_listener":
        e["conditions"] = {"stats_min": {"warmth": 72}, "memory_min": 8}
    if e["id"] == "end_sister_guardian":
        e["conditions"] = {
            "flags_true": ["refused_bride_price"],
            "rel_min": {"ma_xiaoyu": 75},
            "stats_min": {"warmth": 55},
        }

new_endings = [
    {
        "id": "end_village_pillar",
        "title": "沟里的一根柱子",
        "priority": 25,
        "conditions": {
            "stats_min": {"face": 65, "warmth": 55},
            "rel_min": {"sun_youfu": 25, "liu_kuaiji": 15},
            "memory_min": 8,
        },
        "epithet": "一个被具体的人当成靠山的人",
        "body": "你没成大人物。\n\n可孙家有事找你，三叔愿意把账摊给你看，刘会计在议桌上给你留一句公道话。\n\n这不是面子上的热闹，是过日子的底盘。\n\n杏花沟这种地方，柱子不是用来出风头的，是用来在风雨里不塌的。\n\n你塌不了。",
    },
    {
        "id": "end_craftsman",
        "title": "手里有活路的人",
        "priority": 32,
        "conditions": {"stats_min": {"craft": 70, "guts": 50}},
        "epithet": "一个把本事攥在手里的人",
        "body": "算账、认药、写字、理人情——这些不体面，也不虚。\n\n王校长说：人不能光靠志气。你后来懂了：志气要长在本事上。\n\n开春不管走不走，你饿不死。\n\n这世上最踏实的骄傲，是明天也有活干。",
    },
    {
        "id": "end_kind_but_poor",
        "title": "心热钱凉",
        "priority": 70,
        "conditions": {
            "stats_min": {"warmth": 70},
            "stats_max": {"money": 40},
        },
        "epithet": "一个把钱花光了、把人心捂热了的人",
        "body": "账是紧的，心是满的。\n\n你借出的粮、垫的学费、添的份子，一样样都是真的。你自己吃得很省，却常有人念你。\n\n有人说你傻。你笑笑。\n\n穷不是美德，可穷还愿意伸手的人，配被人记住。",
    },
    {
        "id": "end_family_honest",
        "title": "一家人吃一顿踏实饭",
        "priority": 45,
        "conditions": {
            "flags_true": ["confessed_plan"],
            "rel_min": {"he_xiuying": 55, "ma_xiaoyu": 55},
        },
        "epithet": "一个把话说进家里的人",
        "body": "你没许愿，没吹牛。你把打算摊在桌面上。\n\n娘夹给你的那个饺子，比什么都实在。\n\n外面的事再大，家能坐下来吃一顿说真话的饭，这一年就不算白过。\n\n你要走要留，家人是知道的。这就够了。",
    },
]
for e in new_endings:
    if e["id"] not in ids:
        endings.append(e)

ep.write_text(json.dumps(endings, ensure_ascii=False, indent=2), encoding="utf-8")
print("scenes", len(scenes), "endings", len(endings))
