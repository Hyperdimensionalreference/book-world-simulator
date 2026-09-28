# -*- coding: utf-8 -*-
"""新增分支场景：穷人家、宗族、手艺、镇上、说亲支线、延迟后果。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "data" / "samples" / "xinghuagou" / "package"
SCENES = PKG / "scenes.json"

NEW_SCENES = [
  # ========== 早季：资源与人情 ==========
  {
    "id": "s_sun_borrow_grain",
    "title": "半升粮",
    "turn": 1,
    "place": "sun_home",
    "npcs": ["sun_youfu", "sun_dama"],
    "trigger": {"type": "window", "start": 1, "end": 3},
    "narration": "孙家院墙塌了半边，拿泥糊着。锅里是水多菜少。\n\n孙有福搓着手站在门口：「小满……家里见底了。借半升粮，开春就还。」\n\n孙大妈在灶门口，没抬头。娃的书包挂在钉子上，书角卷着。\n\n你家粮也不宽裕。娘说过：穷不帮穷，谁帮。",
    "choices": [
      {
        "id": "c_lend_grain_half",
        "text": "借半升。人不能眼看着邻居断顿。",
        "requirements": {"stats": {"grain": {"min": 1}}},
        "immediate": "孙有福接过粮袋，手抖了一下。「记着的。」他说。\n\n孙大妈朝你福了福身。娃从门缝里看你，眼睛亮。",
        "effects": {
          "stats": {"grain": -1, "warmth": 6, "favor_out": 1},
          "relationships": {"sun_youfu": 12, "sun_dama": 10},
          "flags": {"helped_sun_grain": True},
          "add_memory": ["你借给孙家半升粮", "sun_youfu|小满是能开口的人"],
          "add_note": "一升粮，记在孙家灶台上"
        },
        "hooks": [
          {"delay": 3, "type": "message", "text": "孙有福在量地那天替你家说了句：「马家不是欺负人的。」他嘴笨，话却硬。", "actor": "sun_youfu", "relationships": {"sun_youfu": 6}, "stats": {"face": 3}},
          {"delay": 8, "type": "message", "text": "孙家娃捡了你家一把柴放在门口。小人情，也是大记得。", "actor": "sun_dama", "relationships": {"sun_dama": 5}, "stats": {"warmth": 3}},
          {"delay": 12, "type": "message", "text": "年关时孙家硬凑了半升粮还你，还多拿两个鸡蛋。你推回去，他们硬塞。", "relationships": {"sun_youfu": 8}, "stats": {"favor_out": 0, "warmth": 4}, "actor": "sun_youfu"}
        ],
        "tags": ["人情", "粮"]
      },
      {
        "id": "c_lend_grain_full",
        "text": "多借一升。娃不能饿着长身体。",
        "requirements": {"stats": {"grain": {"min": 2}}},
        "immediate": "你把粮袋又掏了掏。孙有福眼睛红了，没说谢，只把你的手握了一下。\n\n「小满，」孙大妈说，「你是有菩萨心的。」\n\n你回家怎么跟娘交代，是另一回事。",
        "effects": {
          "stats": {"grain": -2, "warmth": 10, "favor_out": 2, "guts": 2},
          "relationships": {"sun_youfu": 18, "sun_dama": 15},
          "flags": {"helped_sun_grain": True, "helped_sun_generous": True},
          "add_memory": ["你多借了孙家粮", "sun_youfu|这份情比命重"],
          "add_note": "你把自家的口袋掏浅了"
        },
        "hooks": [
          {"delay": 2, "type": "message", "text": "娘数落你：「自家都不够，倒充大方！」她骂完，把自己的半块饼子拨给了小雨。", "actor": "he_xiuying", "relationships": {"he_xiuying": -4}},
          {"delay": 5, "type": "message", "text": "孙有福在宗祠议事时站你这边，说：「马家小子心正。」有人嗤笑，他脖子红了也没改口。", "actor": "sun_youfu", "relationships": {"sun_youfu": 8}, "stats": {"face": 4}},
          {"delay": 11, "type": "message", "text": "孙大妈帮你补了两件冬衣，针脚细。她说：「我们没别的，就是有力气和心。」", "actor": "sun_dama", "relationships": {"sun_dama": 8}, "stats": {"warmth": 5, "health": 3}}
        ],
        "tags": ["人情", "厚道"]
      },
      {
        "id": "c_refuse_grain",
        "text": "咬牙说自家也紧。不是不帮，是帮不起。",
        "immediate": "孙有福点点头，没多说：「理解，理解。」\n\n他转身回屋。孙大妈的头低下去。\n\n门关上时，你听见娃问：「娘，有饭吗？」",
        "effects": {
          "stats": {"guts": -2, "warmth": -6},
          "relationships": {"sun_youfu": -8, "sun_dama": -6},
          "flags": {"refused_sun_grain": True},
          "add_memory": ["孙家借粮，你没借"],
          "add_note": "你把一扇门轻轻关上了"
        },
        "hooks": [
          {"delay": 4, "type": "message", "text": "孙有福没说你坏话。可他再借东西，绕开你家门走。那种远，比骂难堪。", "actor": "sun_youfu", "relationships": {"sun_youfu": -4}},
          {"delay": 9, "type": "message", "text": "村里有人提起「马家心硬」。话不重，落在你心里重。", "stats": {"face": -3}, "actor": "village"}
        ],
        "tags": ["拒绝"]
      }
    ]
  },
  {
    "id": "s_craft_apprentice",
    "title": "学一样能换饭的本事",
    "turn": 2,
    "place": "home",
    "npcs": ["ma_changgui", "zhou_dehou"],
    "trigger": {"type": "window", "start": 2, "end": 4},
    "narration": "三叔把软皮本翻到新的一页：「你爹在时，算账是把式。你要学，叔教你。」\n\n卫生所那边，周医生也在找人帮忙抄药方、认药材。\n\n手艺这东西，年轻时不肯弯腰，老了弯腰没人要。",
    "choices": [
      {
        "id": "c_learn_accounting",
        "text": "跟三叔学算账、理人情本。",
        "immediate": "三叔点头：「账是死的，人是活的。你先把死的学会，再学活的。」\n\n他教你怎么记、怎么核、怎么留情面。灯光下，软皮本上的字像蚂蚁排队。",
        "effects": {
          "stats": {"craft": 10, "guts": 3, "face": 2},
          "relationships": {"ma_changgui": 10},
          "flags": {"learned_accounting": True},
          "add_memory": ["你跟三叔学了算账", "ma_changgui|这孩子坐得住"],
          "add_note": "你手里多了一样本事"
        },
        "hooks": [
          {"delay": 2, "type": "message", "text": "王校长让你帮学校核对转学名单，你算得清楚。他多看了你两眼。", "actor": "wang_xiaozhang", "relationships": {"wang_xiaozhang": 6}, "stats": {"craft": 4, "face": 3}},
          {"delay": 6, "type": "message", "text": "年关清账时你帮三叔理了一晚上账，他把余下的零头抹了：「算你学费。」", "actor": "ma_changgui", "stats": {"money": 30, "craft": 5}, "relationships": {"ma_changgui": 5}}
        ],
        "tags": ["手艺", "账"]
      },
      {
        "id": "c_learn_medicine",
        "text": "去卫生所跟周医生认药材、抄方子。",
        "immediate": "周医生把药箱打开：「当归、甘草、陈皮……认全了，饿不死。」\n\n他又说：「李老栓那样的病，光药不够，得养。养，就是要有人。」\n\n你在药味里泡了一下午。",
        "effects": {
          "stats": {"craft": 10, "warmth": 4, "health": -2},
          "relationships": {"zhou_dehou": 12},
          "flags": {"learned_medicine": True},
          "add_memory": ["你跟周医生认了药材"],
          "add_note": "药味沾在袖口上，也沾在命里"
        },
        "hooks": [
          {"delay": 3, "type": "message", "text": "你懂了「得养着」三个字的分量。李老栓病重时，你比别人更知道该做什么。", "stats": {"warmth": 3, "craft": 3}, "flags": {"understand_care": True}, "actor": "zhou_dehou"},
          {"delay": 5, "type": "message", "text": "有人请你帮着看看是不是该叫周医生。小人情，你成了半个明白人。", "stats": {"face": 3, "craft": 2}, "actor": "village"}
        ],
        "tags": ["手艺", "医"]
      },
      {
        "id": "c_skip_craft",
        "text": "眼下事太多，手艺先放放。",
        "immediate": "「过阵子吧。」\n\n三叔合上本子：「过阵子，过阵子，你爹当年也爱说这三个字。」\n\n周医生那边你没去。���味好像也淡了。",
        "effects": {
          "stats": {"guts": -2},
          "flags": {"skipped_craft": True},
          "add_memory": ["你没肯弯腰学手艺"],
          "add_note": "本事没有自己长出来的"
        },
        "hooks": [
          {"delay": 4, "type": "message", "text": "要抄写、算账的活落在别人头上。有人斜你一眼：「有力气不用正地儿。」", "stats": {"craft": -2, "face": -2}, "actor": "village"}
        ],
        "tags": ["错过"]
      }
    ]
  },
  {
    "id": "s_letter_writing",
    "title": "代写一封家信",
    "turn": 3,
    "place": "village",
    "npcs": ["wang_shen", "guihua"],
    "trigger": {"type": "window", "start": 3, "end": 6},
    "narration": "王婶把一张纸按在你手里：「桂花她娘不识字，你给写写。就说家里都好，别叫她挂心。」\n\n纸上已经歪歪扭扭画了几个字，像小娃的笔迹。\n\n桂花在城里打工。信里的「都好」，是真的都好吗？",
    "choices": [
      {
        "id": "c_write_true",
        "text": "写实情：家里难，但盼她好。",
        "immediate": "你把难处写清楚，也写了「莫寄钱太多，顾好自己」。\n\n王婶看了半天：「你这孩子……写得太实了。」\n\n她嘴上嫌，还是把信折好了。",
        "effects": {
          "stats": {"craft": 5, "warmth": 4, "face": 2},
          "relationships": {"wang_shen": 6, "guihua": 8},
          "flags": {"wrote_true_letter": True},
          "add_memory": ["你替孙家/王婶这边写了实情家信"],
          "add_note": "你把实话写进了信里"
        },
        "hooks": [
          {"delay": 3, "type": "message", "text": "桂花寄回一封信，问「是哪个哥哥写的」，还捎了一双鞋垫给「写字实诚的人」。", "actor": "guihua", "relationships": {"guihua": 8}, "stats": {"favor_out": 1}},
          {"delay": 7, "type": "message", "text": "桂花回来探亲时，当面谢你。她说城里人写字好听，可没人肯写真话。", "actor": "guihua", "relationships": {"guihua": 6}, "stats": {"warmth": 3}}
        ],
        "tags": ["信", "实诚"]
      },
      {
        "id": "c_write_pretty",
        "text": "写好看些：一切都好，勿念。",
        "immediate": "你把字写得工工整整：「家中安好，勿念。」\n\n王婶满意了：「这就对了，别叫她在外面哭。」\n\n可你心里清楚：有些不好，被你写没了。",
        "effects": {
          "stats": {"craft": 2, "face": 3, "warmth": -1},
          "relationships": {"wang_shen": 8},
          "flags": {"wrote_pretty_letter": True},
          "add_memory": ["你写了一封报喜不报忧的信"],
          "add_note": "体面，有时是一层纸"
        },
        "hooks": [
          {"delay": 4, "type": "message", "text": "桂花以为家里宽裕，多寄了钱回来，自己在城里吃得很省。后来她知道了，心里硌了一下。", "actor": "guihua", "relationships": {"guihua": -3}, "stats": {"warmth": -2}}
        ],
        "tags": ["信", "体面"]
      }
    ]
  },

  # ========== 中季：宗族 / 钱 / 说亲支线 ==========
  {
    "id": "s_linzi_borrow",
    "title": "堂弟的难处",
    "turn": 5,
    "place": "home",
    "npcs": ["ma_linzi", "ma_changgui"],
    "trigger": {"type": "window", "start": 5, "end": 8},
    "narration": "马林子来了，嘴甜得像抹了蜜：「哥，咱谁跟谁。」\n\n他要借两百块——说亲要用，「就周转一下」。\n\n三叔在门口咳了一声：「软皮本还没写完呢。」\n\n林子脸皮厚：「三叔，您这是帮里不帮亲？」",
    "choices": [
      {
        "id": "c_lend_linzi",
        "text": "借给他。本家的人，不能看着他黄了亲。",
        "requirements": {"stats": {"money": {"min": 120}}},
        "immediate": "林子连连作揖：「哥！你是我亲哥！」\n\n三叔叹气，在本子上写了一行：「借出——马小满——林子。」\n\n你看了一眼，心里也写了一行。",
        "effects": {
          "stats": {"money": -120, "face": 5, "favor_out": 1},
          "relationships": {"ma_linzi": 15, "ma_changgui": -2},
          "flags": {"lent_linzi": True},
          "add_memory": ["你借给堂弟林子钱说亲", "ma_linzi|我哥仁义"],
          "add_note": "软皮本上多了一笔"
        },
        "hooks": [
          {"delay": 3, "type": "message", "text": "林子说亲成了，席面上敬你三杯酒，话说得漂亮。三叔在旁边记账，眼皮没抬。", "actor": "ma_linzi", "relationships": {"ma_linzi": 8}, "stats": {"face": 4}},
          {"delay": 9, "type": "message", "text": "开春林子还钱，只还了八十，说「剩下的缓缓」。他还笑嘻嘻的。你心里有点凉。", "actor": "ma_linzi", "relationships": {"ma_linzi": -6}, "stats": {"money": 80, "favor_in": 1, "guts": -2}}
        ],
        "tags": ["宗族", "借钱"]
      },
      {
        "id": "c_lend_half_linzi",
        "text": "借一半。帮急不帮穷大方。",
        "requirements": {"stats": {"money": {"min": 60}}},
        "immediate": "「就这些。你也自己使劲。」\n\n林子脸色淡了一瞬，又笑：「够了够了，哥！」\n\n他走后，三叔说：「有分寸。借钱这事，亲兄弟也得有分寸。」",
        "effects": {
          "stats": {"money": -60, "guts": 3, "craft": 2},
          "relationships": {"ma_linzi": 5, "ma_changgui": 6},
          "flags": {"lent_linzi_half": True},
          "add_memory": ["你只借了堂弟一半"],
          "add_note": "你把分寸拿捏住了"
        },
        "hooks": [
          {"delay": 8, "type": "message", "text": "林子先还了你的那一半，倒是痛快。他说：「亲兄弟，明算账，我才敢借第二回。」", "actor": "ma_linzi", "relationships": {"ma_linzi": 4}, "stats": {"money": 60}, "stats_note": "先还"}
        ],
        "tags": ["宗族", "分寸"]
      },
      {
        "id": "c_refuse_linzi",
        "text": "不借。我自己还有一屁股账。",
        "immediate": "林子的笑容挂不住了：「哥，你也太……」\n\n「我太什么？」你说，「我爹看病欠的账，你替我还过一文？」\n\n屋里静了。三叔点点头。\n\n林子摔门走了。",
        "effects": {
          "stats": {"guts": 6, "face": -3},
          "relationships": {"ma_linzi": -12, "ma_changgui": 5},
          "flags": {"refused_linzi": True},
          "add_memory": ["你拒绝借钱给堂弟林子"],
          "add_note": "你把一扇亲戚的门关上了一点"
        },
        "hooks": [
          {"delay": 3, "type": "message", "text": "林子在背后说你「发达了六亲不认」。传到你耳朵里，你没回嘴。", "actor": "ma_linzi", "relationships": {"ma_linzi": -5}, "stats": {"face": -3}},
          {"delay": 10, "type": "message", "text": "后来你自己紧的时候，林子没露面。人情是镜子。", "actor": "ma_linzi", "stats": {"guts": 2}}
        ],
        "tags": ["宗族", "拒绝"]
      }
    ]
  },
  {
    "id": "s_ancestral_meeting",
    "title": "宗祠里的摊派",
    "turn": 5,
    "place": "ancestral",
    "npcs": ["ma_changgui", "liu_kuaiji", "zhao_jinsuo", "wang_shen"],
    "trigger": {"type": "window", "start": 5, "end": 6},
    "narration": "马家宗祠开了门。刘会计在念条目：修渠、办席、给孤老的照应银……一样一样摊下来。\n\n赵金锁嗓门大：「有的家该多出！」眼睛往你这边瞟。\n\n三叔把软皮本抱在怀里，像抱个盾牌。\n\n轮到你家表态了。人在看。",
    "choices": [
      {
        "id": "c_pay_share_fair",
        "text": "按丁出份子，不争不躲。",
        "immediate": "你报了数。刘会计记下，说了句「马家按规矩」。\n\n赵金锁哼了一声，没找到茬。\n\n祠堂里的空气松了半分。",
        "effects": {
          "stats": {"money": -40, "face": 5, "guts": 2},
          "relationships": {"liu_kuaiji": 6, "ma_changgui": 4, "zhao_jinsuo": -2},
          "flags": {"paid_ancestral_share": True},
          "add_memory": ["宗祠摊派你按规矩出了钱"],
          "add_note": "你买了个「规矩人」的名"
        },
        "hooks": [
          {"delay": 4, "type": "message", "text": "后来量地议事，刘会计说「马家一直按规矩来」。这句话比十块钱重。", "actor": "liu_kuaiji", "relationships": {"liu_kuaiji": 5}, "stats": {"face": 3}}
        ],
        "tags": ["宗族", "规矩"]
      },
      {
        "id": "c_argue_less_share",
        "text": "开口：家里有病人账，请求少摊些。",
        "immediate": "你站出来，话说得慢，但清楚：爹的病账、妹妹的亲事、地还说不清。\n\n有人撇嘴。孙有福在角落里轻轻点了一下头。\n\n刘会计皱眉：「特殊情况，可以再议。」\n\n赵金锁笑了：「马家也会哭穷了。」",
        "effects": {
          "stats": {"money": -15, "guts": 5, "face": -4},
          "relationships": {"sun_youfu": 6, "liu_kuaiji": -2, "zhao_jinsuo": -6},
          "flags": {"argued_ancestral_share": True},
          "add_memory": ["你在宗祠里为自家争取少摊"],
          "add_note": "你把难处摆上了台面"
        },
        "hooks": [
          {"delay": 2, "type": "message", "text": "有人背后说马家精明、会哭。也有人说他家是真难。名这种东西，裂开就是裂开了。", "stats": {"face": -3}, "actor": "village"},
          {"delay": 6, "type": "message", "text": "孙有福后来还粮时多塞了半升，说：「你敢说话，我佩服。」", "actor": "sun_youfu", "relationships": {"sun_youfu": 6}, "stats": {"warmth": 3}}
        ],
        "tags": ["宗族", "硬话"]
      },
      {
        "id": "c_volunteer_more",
        "text": "主动多认一份，给孤老凑照应银。",
        "immediate": "你举手：「我再认一份。沟口的老人，大家都不易。」\n\n祠堂里静了一下。\n\n三叔看你的眼神复杂：傻，可也有点别的。\n\n赵金锁撇嘴：「充大头。」",
        "effects": {
          "stats": {"money": -55, "face": 8, "warmth": 8, "favor_out": 1},
          "relationships": {"ma_changgui": 2, "li_laoshuan": 8, "li_jianguo": 4, "zhao_jinsuo": -4},
          "flags": {"volunteered_elder_share": True},
          "add_memory": ["你在宗祠多认了照应孤老的份子"],
          "add_note": "你把钱花在了还没病倒的人身上"
        },
        "hooks": [
          {"delay": 3, "type": "message", "text": "李老栓听说后，让人捎话：「小满，我知道。」他一辈子不谢人，这句已经是极重。", "actor": "li_laoshuan", "relationships": {"li_laoshuan": 8}, "stats": {"warmth": 4}},
          {"delay": 7, "type": "message", "text": "李建国回来，先提了你多出照应银的事。他在人前没说谢，眼睛说了。", "actor": "li_jianguo", "relationships": {"li_jianguo": 10}, "stats": {"favor_out": 1}}
        ],
        "tags": ["宗族", "厚道"]
      }
    ]
  },
  {
    "id": "s_guihua_city_truth",
    "title": "城里捎回的话",
    "turn": 7,
    "place": "village",
    "npcs": ["guihua", "zhao_xiaojun"],
    "trigger": {"type": "window", "start": 7, "end": 10},
    "narration": "桂花回来了，指甲剪得短，手却白了些。她说话快：「厂里是挣钱，也熬人。一天站十二个钟头。」\n\n赵小军在旁边笑：「你别听她吓唬人，出去见世面。」\n\n桂花瞥他一眼：「世面是好见的？」\n\n他们说的，是同一个城，又好像不是。",
    "choices": [
      {
        "id": "c_listen_guihua",
        "text": "仔细听桂花说真话，问工钱、工时、病假。",
        "immediate": "桂花掰着手指数：「一月一千八，加班才有。住大通铺。病了自己扛。」\n\n「可留在村里呢？」她反问你。\n\n你也答不上。\n\n赵小军在旁边嘟囔：「就你想得细。」",
        "effects": {
          "stats": {"craft": 4, "guts": 2},
          "relationships": {"guihua": 10, "zhao_xiaojun": -2},
          "flags": {"knows_city_truth": True},
          "add_memory": ["你听桂花讲了城里的真话"],
          "add_note": "你把「出去」两个字称过分量"
        },
        "hooks": [
          {"delay": 2, "type": "message", "text": "赵小军说你「婆婆妈妈」。可李建国后来跟你交底时，更愿意跟想得细的人说话。", "actor": "li_jianguo", "relationships": {"li_jianguo": 5}},
          {"delay": 8, "type": "message", "text": "走还是留的那晚，你没有只被「一月一千八」冲昏头。真话挡了一下虚火。", "stats": {"guts": 4, "craft": 2}, "flags": {"balanced_view_city": True}}
        ],
        "tags": ["城里", "真话"]
      },
      {
        "id": "c_listen_xiaojun",
        "text": "更信赵小军那套：出去闯。",
        "immediate": "小军来劲了：「就是！窝在沟里有啥出息！」\n\n桂花在旁边喝水，没再说话。\n\n你心里的天平，往外面晃了晃。",
        "effects": {
          "stats": {"guts": 3},
          "relationships": {"zhao_xiaojun": 10, "guihua": -4},
          "flags": {"swayed_by_xiaojun": True},
          "add_memory": ["你更倾向信赵小军的话"],
          "add_note": "远方的光，有时会晃眼"
        },
        "hooks": [
          {"delay": 5, "type": "message", "text": "真到要走的时候，你才慢慢咂摸出桂花没说完的那些苦。", "stats": {"guts": -2}, "flags": {"later_doubts_city": True}}
        ],
        "tags": ["城里", "憧憬"]
      }
    ]
  },
  {
    "id": "s_meet_chen_aguo",
    "title": "陈家那孩子",
    "turn": 9,
    "place": "chen_home",
    "npcs": ["chen_aguo", "chen_meipo", "ma_xiaoyu"],
    "trigger": {"type": "window", "start": 9, "end": 11},
    "narration": "陈媒婆把陈阿国推到前头：「就是他。老实孩子。」\n\n阿国站在那儿，手不知道往哪放：「小满哥。」\n\n他看了小雨一眼，又飞快挪开。\n\n「俺爹说，」他开口就是这句，「彩礼是体面。」\n\n说完他自己脸红了。",
    "choices": [
      {
        "id": "c_size_up_aguo",
        "text": "单独问他：你自己是怎么想的？",
        "immediate": "阿国愣住，像没被人这么问过。\n\n「我……」他搓手，「我没别的意思。小雨她，念书好吗？」\n\n这一句，倒有点像真心。\n\n你心里的秤，动了。",
        "effects": {
          "stats": {"warmth": 4, "guts": 2},
          "relationships": {"chen_aguo": 10, "ma_xiaoyu": 4},
          "flags": {"probed_aguo": True, "aguo_ok_person": True},
          "add_memory": ["你私下问了陈阿国的想法", "chen_aguo|他把我当个人问"],
          "add_note": "你看见了包办里那点真心"
        },
        "hooks": [
          {"delay": 2, "type": "message", "text": "阿国偷偷问你小雨爱吃什么，说想买，又怕唐突。他不是恶人，只是被规矩捆着。", "actor": "chen_aguo", "relationships": {"chen_aguo": 6}},
          {"delay": 6, "type": "message", "text": "彩礼谈判时，阿国在他爹跟前小声说了句「别太难为人家」。虽没顶用，你记下了。", "actor": "chen_aguo", "relationships": {"chen_aguo": 5}, "stats": {"warmth": 3}}
        ],
        "tags": ["说亲", "真心"]
      },
      {
        "id": "c_warn_aguo",
        "text": "正告他：不许欺负小雨。",
        "immediate": "你盯着他：「她要是受委屈，我不会看着。」\n\n阿国退了半步：「我、我不敢。」\n\n陈媒婆打圆场：「哎哟，这是疼妹子，疼妹子。」\n\n小雨在门外，没进来。",
        "effects": {
          "stats": {"guts": 6, "face": 2},
          "relationships": {"chen_aguo": 2, "ma_xiaoyu": 8, "chen_meipo": -3},
          "flags": {"warned_aguo": True},
          "add_memory": ["你警告过陈阿国不许欺负小雨"],
          "add_note": "你把哥哥的样子做出来了"
        },
        "hooks": [
          {"delay": 3, "type": "message", "text": "陈家觉得你「厉害」，谈彩礼时又硬了三分。护短有价。", "stats": {"face": 2}, "flags": {"bride_harder": True}, "actor": "chen_meipo"}
        ],
        "tags": ["说亲", "护妹"]
      },
      {
        "id": "c_be_polite",
        "text": "客客气气，不表态。",
        "immediate": "你笑笑，说了几句场面话。\n\n阿国松了口气。陈媒婆很满意。\n\n可小雨看你的眼神，淡了一下。\n\n她可能希望你多问一句。",
        "effects": {
          "stats": {"face": 2, "warmth": -2},
          "relationships": {"chen_meipo": 5, "ma_xiaoyu": -3, "chen_aguo": 3},
          "add_memory": ["你对陈阿国只是客气"],
          "add_note": "礼数全了，心事空着"
        },
        "hooks": [],
        "tags": ["说亲", "客套"]
      }
    ]
  },
  {
    "id": "s_zhen_errand",
    "title": "镇上跑一趟",
    "turn": 11,
    "place": "zhen",
    "npcs": ["zhen_wang", "zhou_dehou"],
    "trigger": {"type": "window", "start": 11, "end": 13},
    "narration": "镇上人多话杂。你要办的事有几件：帮周医生进药、问王干事撤并后的安置、顺道打听工价。\n\n时间只够你把一件办扎实。\n\n王干事的文件夹边角磨白了，他还在用。",
    "choices": [
      {
        "id": "c_clinic_supply",
        "text": "先帮周医生进药，把李老栓要用的备上。",
        "immediate": "你在药铺来回比价，磨了半天。\n\n周医生点头：「会过日子，也会疼人。」\n\n药备上了。治不治得好是命数，备不备是人心。",
        "effects": {
          "stats": {"money": -35, "craft": 4, "warmth": 5, "health": -2},
          "relationships": {"zhou_dehou": 10, "li_laoshuan": 6},
          "flags": {"stocked_medicine": True},
          "add_memory": ["你进镇为李老栓备了药"],
          "add_note": "你把药味背回了村"
        },
        "hooks": [
          {"delay": 2, "type": "message", "text": "病重那几日，药能跟上。周医生说：「幸好早备。」这话你听着不轻松，又踏实。", "actor": "zhou_dehou", "relationships": {"zhou_dehou": 5}, "stats": {"warmth": 3}},
          {"delay": 5, "type": "message", "text": "李建国后来算药钱时，把你垫的那部分还上，又多给了一点。他不欠人的性子。", "actor": "li_jianguo", "stats": {"money": 40}, "relationships": {"li_jianguo": 6}}
        ],
        "tags": ["药", "照应"]
      },
      {
        "id": "c_zhen_job",
        "text": "跑工价、问活路，为自己铺一条道。",
        "immediate": "你问了三家：小工、仓库、饭馆帮厨。\n\n王干事在茶摊上看见你：「年轻人有心。有困难可以反映。」\n\n你把工价记在心里：比村里高，比想象中苦。",
        "effects": {
          "stats": {"money": 15, "craft": 6, "guts": 3},
          "relationships": {"zhen_wang": 5},
          "flags": {"scouted_job": True},
          "add_memory": ["你去镇上打听了活路"],
          "add_note": "你的口袋空着，眼睛亮着"
        },
        "hooks": [
          {"delay": 3, "type": "message", "text": "食堂那个缺你比别人早知道价码，谈的时候心里有底。", "stats": {"craft": 3, "money": 20}, "flags": {"knows_wage": True}},
          {"delay": 6, "type": "message", "text": "周医生那边你没帮上进药，他嘴上不说，眼神淡了些。", "actor": "zhou_dehou", "relationships": {"zhou_dehou": -3}}
        ],
        "tags": ["镇上", "出路"]
      },
      {
        "id": "c_zhen_school",
        "text": "去打听镇中学，给小雨问前程。",
        "immediate": "你把学费、住宿、成绩要求一样样问清。\n\n王干事看了你一眼：「还有心思供妹妹念书？」\n\n「有。」\n\n他说：「按文件来，但……难能可贵。」",
        "effects": {
          "stats": {"craft": 3, "warmth": 6, "money": -10},
          "relationships": {"ma_xiaoyu": 12, "zhen_wang": 3},
          "flags": {"asked_sister_school": True},
          "add_memory": ["你为小雨去镇上问了中学"],
          "add_note": "你把她的前程当公事办了"
        },
        "hooks": [
          {"delay": 2, "type": "message", "text": "小雨知道后，在本子上写：哥，我会考上的。字很重，把纸都压凹了。", "actor": "ma_xiaoyu", "relationships": {"ma_xiaoyu": 8}, "stats": {"warmth": 4}},
          {"delay": 7, "type": "message", "text": "王校长听说你跑镇中，把该他跑的那份材料也帮你问了。教书人认这种人。", "actor": "wang_xiaozhang", "relationships": {"wang_xiaozhang": 8}, "stats": {"favor_out": 1}}
        ],
        "tags": ["妹妹", "念书"]
      }
    ]
  },
  {
    "id": "s_health_collapse",
    "title": "身子要账",
    "turn": 13,
    "place": "clinic",
    "npcs": ["zhou_dehou", "he_xiuying"],
    "trigger": {"type": "window", "start": 13, "end": 15},
    "narration": "你蹲下去再站起来时，眼前黑了一下。\n\n娘按住你的肩：「去卫生所。」\n\n周医生听了听，又按了按：「累狠了。得养着。」\n\n「养着」要时间，可年关、账、亲事，哪一个都不等人。",
    "choices": [
      {
        "id": "c_rest_med",
        "text": "听医嘱，歇两天，把药吃了。",
        "immediate": "你躺在家里，听见娘在外屋数钱。\n\n小雨把热水端进来：「哥，你别硬撑了。」\n\n药苦。可你确实好了些。",
        "effects": {
          "stats": {"health": 18, "money": -25, "guts": -2, "warmth": 3},
          "relationships": {"he_xiuying": 6, "ma_xiaoyu": 5, "zhou_dehou": 4},
          "flags": {"rested_when_sick": True},
          "add_memory": ["你病了，听医嘱歇了"],
          "add_note": "你向自己的身体低了头"
        },
        "hooks": [
          {"delay": 2, "type": "message", "text": "后来白事上你能撑到底，没中途垮。身子记仇，也记好。", "stats": {"health": 5}}
        ],
        "tags": ["身体"]
      },
      {
        "id": "c_work_through",
        "text": "扛着。事情不等人。",
        "immediate": "「没事。」\n\n你又去干活。手有点抖，心里还硬着。\n\n周医生摇头走了。\n\n娘在你背后，把药包放在了门槛上。",
        "effects": {
          "stats": {"health": -12, "money": 20, "guts": 6, "craft": 2},
          "relationships": {"he_xiuying": -3, "zhou_dehou": -2},
          "flags": {"overworked": True},
          "add_memory": ["你病了还硬扛"],
          "add_note": "你把命当鞭子使"
        },
        "hooks": [
          {"delay": 1, "type": "message", "text": "夜里咳。小雨给你盖被，你装睡。", "stats": {"health": -4}, "actor": "ma_xiaoyu"},
          {"delay": 4, "type": "message", "text": "丧事那几日你眼前又黑过一回，全靠年轻扛住。周医生说：「再熬就不是养能养回来的。」", "stats": {"health": -6}, "actor": "zhou_dehou"}
        ],
        "tags": ["身体", "硬撑"]
      }
    ]
  },
  {
    "id": "s_son_school_or_work",
    "title": "孙家丫头",
    "turn": 15,
    "place": "sun_home",
    "npcs": ["sun_youfu", "sun_dama"],
    "trigger": {"type": "window", "start": 15, "end": 17},
    "narration": "孙有福蹲在门槛上：「丫头成绩还行……可家里，唉。」\n\n孙大妈补衣裳的手停了：「要不，让她去打工。」\n\n丫头在里屋写字，装作没听见。\n\n你开口，他们就多一分指望。你不开口，这也是他们自己的难。",
    "choices": [
      {
        "id": "c_back_sun_daughter",
        "text": "搭把手：先借点学费，让她把书念完这一年。",
        "requirements": {"stats": {"money": {"min": 40}}},
        "immediate": "「念书的钱，我先垫一点。」\n\n孙有福站起来，膝盖咔吧一声：「小满……」\n\n「别说那个。」你说，「让她念。」",
        "effects": {
          "stats": {"money": -40, "warmth": 10, "favor_out": 2, "craft": 1},
          "relationships": {"sun_youfu": 15, "sun_dama": 12},
          "flags": {"backed_sun_daughter": True},
          "add_memory": ["你资助孙家丫头念书", "sun_youfu|我们家欠小满一条路"],
          "add_note": "你���一条路让给了孩子"
        },
        "hooks": [
          {"delay": 2, "type": "message", "text": "丫头作文里写了你：「小满叔说，念书不是为了离开，是为了回来时有本事。」老师把作文贴在了教室。", "actor": "sun_youfu", "relationships": {"sun_youfu": 6}, "stats": {"warmth": 5, "face": 3}},
          {"delay": 6, "type": "message", "text": "开春孙有福扛活最狠的时候，先来帮你家翻地。他不说谢，用汗说。", "actor": "sun_youfu", "relationships": {"sun_youfu": 10}, "stats": {"favor_out": 1, "warmth": 4}}
        ],
        "tags": ["孩子", "念书"]
      },
      {
        "id": "c_advise_realistic",
        "text": "劝他们想开点：打工也是路。",
        "immediate": "「不是念书才有出息。」\n\n孙大妈点头。孙有福闷头抽烟。\n\n里屋的笔，停了一下，又继续写。\n\n你走时觉得自己说得很现实，也有点残忍。",
        "effects": {
          "stats": {"guts": 2, "warmth": -4},
          "relationships": {"sun_youfu": -3, "sun_dama": -2},
          "flags": {"advised_sun_work": True},
          "add_memory": ["你劝孙家让丫头去打工"],
          "add_note": "你把现实递了过去"
        },
        "hooks": [
          {"delay": 3, "type": "message", "text": "丫头真的去城里了。孙家宽了点，屋里的笑声少了点。孙大妈见你还笑，笑不进眼底。", "actor": "sun_dama", "relationships": {"sun_dama": -4}, "stats": {"warmth": -3}}
        ],
        "tags": ["孩子", "现实"]
      },
      {
        "id": "c_listen_sun",
        "text": "听他们倒苦水，不替他们决定。",
        "immediate": "你就听着。孙有福说地，孙大妈说针线，说来说去，是穷。\n\n说完孙有福自己倒笑了：「跟你说这些干啥。」\n\n你走时，把带的一块干粮放在了窗台上。",
        "effects": {
          "stats": {"warmth": 5},
          "relationships": {"sun_youfu": 8, "sun_dama": 8},
          "add_memory": ["你听孙家倒了苦水"],
          "add_note": "你在场，没乱出主意"
        },
        "hooks": [
          {"delay": 4, "type": "message", "text": "孙家有事更愿意找你商量。信任是慢慢堆的。", "actor": "sun_youfu", "relationships": {"sun_youfu": 5, "sun_dama": 4}}
        ],
        "tags": ["孩子", "倾听"]
      }
    ]
  },
  {
    "id": "s_city_letter",
    "title": "信封上的地址",
    "turn": 17,
    "place": "gate",
    "npcs": ["guihua", "wang_shen"],
    "trigger": {"type": "window", "start": 17, "end": 17},
    "narration": "村口来了车，捎下两封信。\n\n一封是桂花的，一封是写给你家的——陌生地址，像是城里的工厂。\n\n王婶探头：「谁的？谁的？」\n\n风把信封吹得哗哗响。",
    "choices": [
      {
        "id": "c_read_job_letter",
        "text": "拆开工厂的信：是招工/安置的消息。",
        "immediate": "信不长：年后要人，初七前回话。\n\n赵小军探过头：「好机会！」\n\n桂花扫了一眼：「那边住大通铺。」\n\n两张嘴，两座城。",
        "effects": {
          "stats": {"guts": 3, "craft": 2},
          "flags": {"got_job_letter": True},
          "add_memory": ["年后招工信到了你手里"],
          "add_note": "一扇门被推开了一条缝"
        },
        "hooks": [
          {"delay": 1, "type": "message", "text": "你开始想走的那条路。娘夜里纳鞋底，没问你，也没停手。", "actor": "he_xiuying", "relationships": {"he_xiuying": 2}}
        ],
        "tags": ["城里", "信"]
      },
      {
        "id": "c_read_family_first",
        "text": "先管自家的事，信放兜里。",
        "immediate": "你把信叠好放进口袋。\n\n「不急。」\n\n桂花看看你，笑了下：「你能沉住气。」\n\n王婶可沉不住：「哎你倒是说说！」",
        "effects": {
          "stats": {"guts": 2, "warmth": 2},
          "relationships": {"wang_shen": -2, "guihua": 4},
          "add_memory": ["招工信被你压到了年后"],
          "add_note": "你把远方往兜里按了按"
        },
        "hooks": [
          {"delay": 1, "type": "message", "text": "你给这件事留了余地，也留了责任。不是所有门都要立刻闯。", "stats": {"guts": 2, "warmth": 2}}
        ],
        "tags": ["城里", "沉着"]
      }
    ]
  },
  {
    "id": "s_year_end_night",
    "title": "除夜的灯",
    "turn": 18,
    "place": "home",
    "npcs": ["he_xiuying", "ma_xiaoyu"],
    "trigger": {"type": "window", "start": 18, "end": 18},
    "narration": "年三十的灯亮着。\n\n娘把饺子端上来，说：「吃了这个，又长一岁。」\n\n小雨看你：「哥，开春你到底怎么想？」\n\n窗外有人放了零星的炮。\n\n这是你回望自己、也对家人交底的时刻。",
    "choices": [
      {
        "id": "c_confess_plan",
        "text": "把真实打算说出来：走或留，一起扛。",
        "immediate": "你说得慢，把账、打算、难处都摊开。\n\n娘听完，把一个饺子夹到你碗里：「你说的，就照你说的办。」\n\n小雨的眼睛亮了。\n\n灯花爆了一下。",
        "effects": {
          "stats": {"guts": 5, "warmth": 6, "face": 2},
          "relationships": {"he_xiuying": 10, "ma_xiaoyu": 10},
          "flags": {"confessed_plan": True},
          "add_memory": ["除夜你对家人交了底"],
          "add_note": "你把自己的路说成了家的路"
        },
        "hooks": [],
        "tags": ["家", "交底"]
      },
      {
        "id": "c_keep_quiet",
        "text": "不说破：「过了年再说。」",
        "immediate": "「过了年再说。」\n\n娘没再问。小雨低头吃饺子。\n\n有些话，你觉得自己是体贴，他们可能会当成疏远。\n\n灯一直亮到很晚。",
        "effects": {
          "stats": {"warmth": -2, "guts": -1},
          "relationships": {"he_xiuying": -3, "ma_xiaoyu": -2},
          "flags": {"quiet_at_year_end": True},
          "add_memory": ["除夜你没交底"],
          "add_note": "话留在了肚子里"
        },
        "hooks": [],
        "tags": ["家", "沉默"]
      }
    ]
  },
]


def main() -> None:
    scenes = json.loads(SCENES.read_text(encoding="utf-8"))
    existing = {s["id"] for s in scenes}
    added = 0
    for s in NEW_SCENES:
        if s["id"] not in existing:
            scenes.append(s)
            existing.add(s["id"])
            added += 1
    SCENES.write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"scenes now {len(scenes)} (+{added})")


if __name__ == "__main__":
    main()
