# -*- coding: utf-8 -*-
"""杏花沟内容扩充：人物/地点/冲突/数值骨架。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "data" / "samples" / "xinghuagou" / "package"
WORLD = PKG / "world.json"

world = json.loads(WORLD.read_text(encoding="utf-8"))

# ---------- 人物 ----------
existing = {c["id"] for c in world["characters"]}
new_chars = [
    {
        "id": "zhou_dehou",
        "name": "周德厚",
        "age": 56,
        "role": "村医",
        "faction": "卫生所",
        "speech_style": "慢，专业词夹土话，爱说「养着」",
        "speech_examples": ["咳成这样，得养着。", "药贵，命更贵。", "我这是看病，不是看钱。"],
        "wants": "把人治好、别欠卫生所账、有个能接班的",
        "blocks": "药贵、病人拖、自己眼也花",
        "costs": "赊账收不回；说真话得罪家属",
        "summary": "药箱比他的背还沉。",
    },
    {
        "id": "sun_youfu",
        "name": "孙有福",
        "age": 38,
        "role": "邻里穷人",
        "faction": "孙家",
        "speech_style": "低、短，说完就搓手",
        "speech_examples": ["小满……借点粮。", "开春就还。", "我不是不记恩。"],
        "wants": "一家四口不饿、女儿别失学、别被人戳脊梁",
        "blocks": "地少、妻弱、嘴笨",
        "costs": "开口借就是丢脸；不借孩子挨饿",
        "summary": "院墙塌了半边，拿泥糊着。",
    },
    {
        "id": "sun_dama",
        "name": "孙大妈",
        "age": 36,
        "role": "孙有福妻",
        "faction": "孙家",
        "speech_style": "声音细，爱把苦往肚里咽",
        "speech_examples": ["够了够了。", "难为你了。", "娃他爹嘴笨，你别见怪。"],
        "wants": "娃有口热的、别让男人再低头",
        "blocks": "体弱、针线换不来几文",
        "costs": "接受接济就是矮人一头",
        "summary": "灶膛里的火，能省就省。",
    },
    {
        "id": "chen_aguo",
        "name": "陈阿国",
        "age": 20,
        "role": "说亲对象",
        "faction": "陈家",
        "speech_style": "实诚，略木，开口带「俺爹说」",
        "speech_examples": ["俺爹说，彩礼是体面。", "我……我没别的意思。", "小雨她，念书好吗？」"],
        "wants": "把亲事办成、别让爹丢脸、对小雨好",
        "blocks": "爹要彩礼硬、自己没主见",
        "costs": "顺爹伤小雨；护小雨顶撞家",
        "summary": "站在陈媒婆后头，像根还没长直的树。",
    },
    {
        "id": "ma_linzi",
        "name": "马林子",
        "age": 24,
        "role": "堂弟",
        "faction": "马家宗族",
        "speech_style": "滑，嘴甜，遇事往后缩",
        "speech_examples": ["哥，咱谁跟谁。", "三叔那边我去说。", "钱我记着呢！」"],
        "wants": "借钱渡过说亲关、在村里有面子",
        "blocks": "手散、好赌小钱、爹管不住",
        "costs": "借多了伤亲戚；不借落「不顾本家」",
        "summary": "软皮本上很快又会多一行。",
    },
    {
        "id": "zhen_wang",
        "name": "王干事",
        "age": 40,
        "role": "镇上干部",
        "faction": "镇",
        "speech_style": "官话，爱说「按文件来」",
        "speech_examples": ["这是上头精神。", "有困难可以反映。", "按文件来。"],
        "wants": "把差事办完、别出乱子",
        "blocks": "村里关系复杂",
        "costs": "太硬伤和气；太软完不成",
        "summary": "文件夹边角磨白了，他还在用。",
    },
    {
        "id": "guihua",
        "name": "桂花",
        "age": 19,
        "role": "王婶侄女/打工妹",
        "faction": "村中",
        "speech_style": "快、脆，城里的词往外蹦",
        "speech_examples": ["在城里站住脚才算本事。", "小满哥你太实在了���", "外头工资是高，可也熬人。"],
        "wants": "挣嫁妆、别回村种地、有人记得她",
        "blocks": "家里要她寄钱、外头没根",
        "costs": "寄钱掏空自己；不寄被骂没良心",
        "summary": "回来时指甲剪得很短，手却白了些。",
    },
]
for c in new_chars:
    if c["id"] not in existing:
        world["characters"].append(c)

# 补 speech_examples 到旧人物（如有缺）
# ---------- 地点 ----------
existing_p = {p["id"] for p in world["places"]}
new_places = [
    {"id": "clinic", "name": "卫生所", "description": "药味重，周医生的听诊器冰凉。"},
    {"id": "zhen", "name": "镇上", "description": "供销社大些，人杂些，话也虚些。"},
    {"id": "ancestral", "name": "马家宗祠", "description": "议事、摊派、排座次的地方。"},
    {"id": "river", "name": "河沿", "description": "洗菜、说闲话、想心事。"},
    {"id": "gate", "name": "村口", "description": "车停的地方，也是人走的地方。"},
    {"id": "sun_home", "name": "孙家", "description": "泥墙塌半边，娃的书包挂在钉子上。"},
    {"id": "chen_home", "name": "陈家", "description": "门楼新些，规矩也多些。"},
]
for p in new_places:
    if p["id"] not in existing_p:
        world["places"].append(p)

# ---------- 数值 ----------
# 手艺/识字作为软资源，影响帮忙写信、算账、镇上机会
stat_ids = {s["id"] for s in world["stats"]}
if "craft" not in stat_ids:
    world["stats"].append(
        {
            "id": "craft",
            "name": "手艺",
            "start": 35,
            "min": 0,
            "max": 100,
            "description": "识字、算账、农活把式——能换成活路的本事",
        }
    )

# 调整起点，让中期有起伏空间
for s in world["stats"]:
    if s["id"] == "money":
        s["start"] = 220
        s["description"] = "家里可动用的现钱（元）。"
    if s["id"] == "grain":
        s["start"] = 5
        s["max"] = 24
    if s["id"] == "health":
        s["start"] = 78
    if s["id"] == "favor_in":
        s["start"] = 2

# ---------- 世界观注记 ----------
world["resources_note"] = (
    "时间只有一份；钱与粮是硬资源；面子、人情、手艺是软资源，通过具体的人传导回来。"
    "小世界的压力不是拯救村庄，而是：账、脸、学、病、走、留。"
)
world["world_rules"] = [
    "人情债必须记在具体的人身上，并在日后以具体方式回来",
    "面子可以挣、可以让、可以丢；丢了不自动回来",
    "定数（量地/订婚/病故/撤并/年关）不可改写，只能准备与面对",
    "节气与农时决定时间感：不是「第几章」，是「白露该干什么」",
    "开口求人是代价；不开口也是代价",
    "城里的消息既是出路也是抽水机——带走年轻人",
]
if "meta" in world:
    world["meta"]["title"] = "杏花沟 · 一季秋事"
    world["meta"]["intro"] = (
        "立秋刚过。杏花沟的风已经硬了。\n\n"
        "你叫马小满，二十二。爹前年病逝，看病欠下三叔三千块。"
        "娘何秀英要强，妹妹小雨正被说亲。你在村小学帮工——可小学听说要撤并。\n\n"
        "河滩那块地，和赵家界石不清。沟口的李老栓咳得越来越厉害。"
        "隔壁孙家锅里快见底。风声说镇上要重新量地。\n\n"
        "书上写定的事会按期来。你改不了大势。\n"
        "你只能决定：人情往哪儿欠，时间给谁用，脸面值多少，手艺练不练，最后——你成了谁。"
    )

# 定数线索更厚（物价/人际/消失）
rumor_adds = {
    "canon_land_survey": [
        {"turn": 2, "text": "有人看见赵金锁夜里往刘会计家送过东西。", "source": "墙根", "canon_event": "canon_land_survey"},
        {"turn": 3, "text": "镇上喇叭念了「稳定承包关系」，没人细听，可刘会计抄了半页。", "source": "村部", "canon_event": "canon_land_survey"},
    ],
    "canon_zhao_engagement": [
        {"turn": 5, "text": "赵小军在供销社打电话，说「酒席要办得像样」。", "source": "供销社", "canon_event": "canon_zhao_engagement"},
    ],
    "canon_li_illness": [
        {"turn": 7, "text": "周医生从沟口出来，摇着头说「得养着」，药钱却没提。", "source": "路遇", "canon_event": "canon_li_illness"},
    ],
    "canon_li_return": [
        {"turn": 9, "text": "孙有福跟人打听「南边厂子要不要女工」，说完自己先红了脸。", "source": "村中", "canon_event": "canon_li_return"},
    ],
    "canon_bride_pressure": [
        {"turn": 11, "text": "陈家托人问「马家姑娘念到哪了」，像在称斤两。", "source": "传话", "canon_event": "canon_bride_pressure"},
    ],
    "canon_li_death": [
        {"turn": 13, "text": "沟口的狗叫了一夜。周医生的药箱进了又出。", "source": "夜里", "canon_event": "canon_li_death"},
    ],
    "canon_school_close": [
        {"turn": 15, "text": "桌椅上了册子，像要抬走。孩子们还在跳房子。", "source": "学校", "canon_event": "canon_school_close"},
    ],
    "canon_year_end": [
        {"turn": 17, "text": "有人开始躲债，有人开始要债。年关还没到，心先到了。", "source": "村中", "canon_event": "canon_year_end"},
    ],
}
for e in world["canon_events"]:
    add = rumor_adds.get(e.get("id"), [])
    have = {(r.get("turn"), r.get("text")) for r in e.get("rumors") or []}
    for r in add:
        key = (r["turn"], r["text"])
        if key not in have:
            e.setdefault("rumors", []).append(r)

WORLD.write_text(json.dumps(world, ensure_ascii=False, indent=2), encoding="utf-8")
print("world expanded:", len(world["characters"]), "chars", len(world["places"]), "places")
