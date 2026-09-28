# -*- coding: utf-8 -*-
"""补几场主线外的「有事可做」场景 + 软化两极数值。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "data" / "samples" / "xinghuagou" / "package"
SCENES = PKG / "scenes.json"
scenes = json.loads(SCENES.read_text(encoding="utf-8"))
existing = {s["id"] for s in scenes}

EXTRA = [
    {
        "id": "s_help_write_deeds",
        "title": "抄一份文书",
        "turn": 7,
        "place": "accountant",
        "npcs": ["liu_kuaiji", "ma_changgui"],
        "trigger": {"type": "window", "start": 7, "end": 9},
        "narration": "刘会计忙得转圈：量地文书、转学名册、摊派底账都要抄。\n\n「字好、算得清的，」他说，「帮一把。」\n\n三叔看了你一眼：「去吧。这也是学。」\n\n灯要亮到后半夜。",
        "choices": [
            {
                "id": "c_help_clerk",
                "text": "留下抄写核对，把差事办稳。",
                "immediate": "你抄到后半夜，眼睛酸。\n\n刘会计把一份多余的稿费（其实是补贴）推过来：「拿着。别声张。」\n\n「按政策来，」他又补一句，「也看实际情况。」",
                "effects": {
                    "stats": {"craft": 8, "money": 35, "face": 4, "health": -4, "guts": 2},
                    "relationships": {"liu_kuaiji": 10, "ma_changgui": 4},
                    "flags": {"helped_clerk": True},
                    "add_memory": ["你帮刘会计抄了文书"],
                    "add_note": "灯下的字，也是路",
                },
                "hooks": [
                    {
                        "delay": 2,
                        "type": "message",
                        "text": "量地底账你比别人多懂一层。真到要说明白的时候，你有据。",
                        "stats": {"craft": 3, "face": 3},
                        "flags": {"knows_ledger": True},
                        "actor": "liu_kuaiji",
                    }
                ],
                "tags": ["手艺", "村政"],
            },
            {
                "id": "c_help_farm_instead",
                "text": "回去干活，地里的不等人。",
                "immediate": "「地里还有活。」\n\n刘会计点头，没强留。\n\n可他桌上的名字，少了一个马小满。",
                "effects": {
                    "stats": {"grain": 1, "money": 15, "health": -3, "craft": -1},
                    "add_memory": ["你没去抄文书"],
                    "add_note": "你选了土地那边",
                },
                "hooks": [
                    {
                        "delay": 3,
                        "type": "message",
                        "text": "有人顶了抄写的差，也顺手顶了「村里人看好」那一分。",
                        "stats": {"face": -2},
                        "actor": "village",
                    }
                ],
                "tags": ["农时"],
            },
        ],
    },
    {
        "id": "s_river_confession",
        "title": "河沿说话",
        "turn": 10,
        "place": "river",
        "npcs": ["ma_xiaoyu", "guihua"],
        "trigger": {"type": "window", "start": 10, "end": 12},
        "narration": "河沿水浅。小雨在洗一件旧衣裳，桂花蹲在旁边讲城里的事。\n\n「念书好，」桂花说，「可念完了呢？」\n\n小雨把衣裳拧干：「我想考出去。又怕……拖累家里。」\n\n她没看你看，却像在等你接话。",
        "choices": [
            {
                "id": "c_encourage_sister",
                "text": "跟她说：考出去，是给家里争气，不是拖累。",
                "immediate": "「拖累？」你笑了一下，「你要真考出去，咱家祖坟都冒青烟。」\n\n桂花拍手。小雨也笑了，眼圈有点红。\n\n河水在脚边，清得能看见砂。",
                "effects": {
                    "stats": {"warmth": 8, "guts": 3},
                    "relationships": {"ma_xiaoyu": 12, "guihua": 5},
                    "flags": {"encouraged_sister_exam": True},
                    "add_memory": ["河沿上你鼓励小雨考出去"],
                    "add_note": "你把她的心气又扶了一把",
                },
                "hooks": [
                    {
                        "delay": 2,
                        "type": "message",
                        "text": "小雨念书更狠了，夜里点灯到很晚。娘一边骂费油，一边把灯芯拨亮。",
                        "actor": "ma_xiaoyu",
                        "relationships": {"ma_xiaoyu": 6, "he_xiuying": 3},
                    },
                    {
                        "delay": 6,
                        "type": "message",
                        "text": "她后来跟人说：「我哥说这是争气。」这句话在她说亲时，成了她的骨头。",
                        "actor": "ma_xiaoyu",
                        "relationships": {"ma_xiaoyu": 8},
                        "stats": {"warmth": 4, "guts": 3},
                    },
                ],
                "tags": ["妹妹", "河沿"],
            },
            {
                "id": "c_realistic_sister",
                "text": "说实话：考出去也要钱，路还长。",
                "immediate": "「我不是泼冷水。」你说，「学费、路费、往后……都得心里有数。」\n\n小雨点头，笑容淡了些。\n\n桂花白你一眼：「你就不能让她先高兴高兴？」",
                "effects": {
                    "stats": {"craft": 3, "warmth": -2, "guts": 2},
                    "relationships": {"ma_xiaoyu": -4, "guihua": -3},
                    "add_memory": ["河沿上你跟小雨说了现实"],
                    "add_note": "清醒的话，有时割人",
                },
                "hooks": [],
                "tags": ["妹妹", "现实"],
            },
        ],
    },
    {
        "id": "s_zhao_ask_favor",
        "title": "赵家的口",
        "turn": 12,
        "place": "zhao_home",
        "npcs": ["zhao_jinsuo", "zhao_xiaojun"],
        "trigger": {"type": "window", "start": 12, "end": 14},
        "narration": "赵金锁破天荒请你坐：「小满，叔有件事……」\n\n小军在城里要办什么手续，缺个「村里知根知底」的证明人，还想借你家的旧凭据说明邻界。\n\n「不是白用。」赵金锁说，「你开口。」\n\n量地那口气，还在你俩之间飘着。",
        "choices": [
            {
                "id": "c_help_zhao_favor",
                "text": "帮这个忙。一码归一码。",
                "immediate": "「行。」\n\n赵金锁一拍大腿：「痛快！」\n\n小军递烟，你摆手。\n\n出门时你想：这是不是把量地的账勾销了？没有。可人情账本，翻了新的一页。",
                "effects": {
                    "stats": {"favor_out": 1, "face": 4, "guts": 3},
                    "relationships": {"zhao_jinsuo": 12, "zhao_xiaojun": 8},
                    "flags": {"helped_zhao_favor": True},
                    "add_memory": ["你帮赵家出了证明", "zhao_jinsuo|这小子做事有格局"],
                    "add_note": "你把旧怨和新事分开了",
                },
                "hooks": [
                    {
                        "delay": 2,
                        "type": "message",
                        "text": "赵金锁在人前说你「做事敞亮」。后来借板车、传口信，都顺了。",
                        "actor": "zhao_jinsuo",
                        "relationships": {"zhao_jinsuo": 6},
                        "stats": {"face": 3},
                    },
                    {
                        "delay": 5,
                        "type": "message",
                        "text": "小军回城前说：「有事你吱声。」这话虚，也留了钩。",
                        "actor": "zhao_xiaojun",
                        "relationships": {"zhao_xiaojun": 5},
                    },
                ],
                "tags": ["人情", "格局"],
            },
            {
                "id": "c_payback_zhao",
                "text": "先讨一句：量地的事，你得认一句公道。",
                "immediate": "「要我帮，可以。」你说，「量地那天，你当着人说我年轻气盛——这句，你收回去。」\n\n祠堂里一样的空气，回来了。\n\n赵金锁脸涨红，半晌：「……行。算我失言。」\n\n够了。你帮了忙，也把话要回来了。",
                "effects": {
                    "stats": {"guts": 8, "face": 6},
                    "relationships": {"zhao_jinsuo": 6, "zhao_xiaojun": 4},
                    "flags": {"helped_zhao_favor": True, "reclaimed_face_zhao": True},
                    "add_memory": ["你帮了赵家，也讨回了面子", "zhao_jinsuo|这小子，我服半分"],
                    "add_note": "人情不是跪出来的",
                },
                "hooks": [
                    {
                        "delay": 3,
                        "type": "message",
                        "text": "村里有人说：马家小子不软。也有人说他记仇。名是两面的。",
                        "stats": {"face": 4, "guts": 3},
                        "actor": "village",
                    }
                ],
                "tags": ["人情", "硬气"],
            },
            {
                "id": "c_refuse_zhao",
                "text": "不帮。量地的气还没顺。",
                "immediate": "「对不住。这事我办不了。」\n\n赵金锁笑容僵住：「你……行。」\n\n小军在旁边皱眉。门关得很轻，比摔门还冷。",
                "effects": {
                    "stats": {"guts": 2, "face": -2},
                    "relationships": {"zhao_jinsuo": -10, "zhao_xiaojun": -5},
                    "flags": {"refused_zhao_favor": True},
                    "add_memory": ["你拒绝帮赵家"],
                    "add_note": "你把一口气留住了，也把路窄了",
                },
                "hooks": [
                    {
                        "delay": 2,
                        "type": "message",
                        "text": "赵家往后跟你客气，客气就是墙。借东西不好开口了。",
                        "actor": "zhao_jinsuo",
                        "relationships": {"zhao_jinsuo": -4},
                    }
                ],
                "tags": ["拒绝"],
            },
        ],
    },
    {
        "id": "s_craft_choice_late",
        "title": "把式",
        "turn": 14,
        "place": "field",
        "npcs": ["zhou_dehou", "ma_changgui"],
        "trigger": {"type": "window", "start": 14, "end": 16},
        "narration": "白事忙完，人歇地不歇。\n\n你手上的把式已经能看出路数：是算账的，是抓药的，还是庄稼院的。\n\n周医生说：「手艺不怕多。」\n\n三叔说：「专一样，才值钱。」\n\n你得挑一条更深的沟。",
        "choices": [
            {
                "id": "c_deepen_craft",
                "text": "挑一样钻进去：把式练成看家本事。",
                "immediate": "你狠练了一阵。手上起茧，心里有数。\n\n「成了。」周医生/三叔（看你的方向）点头，「以后饿不死。」",
                "effects": {
                    "stats": {"craft": 14, "health": -4, "guts": 4, "face": 3},
                    "flags": {"deepened_craft": True},
                    "add_memory": ["你把手艺练成了看家本事"],
                    "add_note": "你多了一层立身的壳",
                },
                "hooks": [
                    {
                        "delay": 2,
                        "type": "message",
                        "text": "年后不管是进厂还是留村，你的工价都比别人硬气一截。",
                        "stats": {"money": 35, "craft": 5},
                        "flags": {"skilled_hand": True},
                    }
                ],
                "tags": ["手艺"],
            },
            {
                "id": "c_balance_craft",
                "text": "样样通一点，别把自己钉死。",
                "immediate": "你什么都摸了摸。不深，但宽。\n\n有人笑你杂。你想的是：世道一变，专一样的人先慌。",
                "effects": {
                    "stats": {"craft": 7, "guts": 2, "warmth": 2},
                    "add_memory": ["你把手艺练宽了"],
                    "add_note": "你留了转身的余地",
                },
                "hooks": [],
                "tags": ["手艺"],
            },
        ],
    },
]

for s in EXTRA:
    if s["id"] not in existing:
        scenes.append(s)

# 软化：减少「低」路径里刷满面子的无代价加值
for s in scenes:
    for c in s.get("choices") or []:
        st = (c.get("effects") or {}).get("stats") or {}
        # 单次 +face 超过 8 且 money 未减的，压到 6
        if st.get("face", 0) >= 8 and "money" not in st:
            st["face"] = 6
        # 硬气一次别冲太猛
        if st.get("guts", 0) >= 10:
            st["guts"] = 8

SCENES.write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")
print("scenes", len(scenes))
