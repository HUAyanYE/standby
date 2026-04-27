#!/usr/bin/env python3
"""
Standby 种子数据生成器 — 500 条真实感数据

设计原则:
1. 话题多样: 覆盖生活各方面
2. 真情实感: 不是社交表演，是真实表达
3. 多模态: 文本/图片/音频/视频混合
4. 符合产品定位: 匿名、私密、共鸣导向

使用方式:
    cd /mnt/d/Hermes/standby
    python3 scripts/seed_500.py
"""

import json
import random
import time
import uuid
import urllib.request

# ============================================================
# 配置
# ============================================================

GATEWAY_URL = "http://localhost:8080"

# 测试用户 (5 个不同画像)
USERS = [
    {"name": "夜的旅人", "avatar": "🌙", "device": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"},
    {"name": "晨曦行者", "avatar": "☀️", "device": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3"},
    {"name": "微风诗人", "avatar": "🌊", "device": "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"},
    {"name": "秋日守望", "avatar": "🍂", "device": "d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5"},
    {"name": "冬雪归人", "avatar": "❄️", "device": "e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"},
]

# ============================================================
# 锚点数据 — 真实感想，不是社交内容
# ============================================================

ANCHORS = [
    # 童年与成长
    {
        "text": "小时候最喜欢下雨天，因为可以踩水坑。现在下雨天只想着别弄湿鞋。",
        "topics": ["童年", "成长", "下雨"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "整理旧物时翻到小学作文本，写的是'我的梦想是当科学家'。现在在写代码，也算某种意义上的科学家吧。",
        "topics": ["童年", "梦想", "成长"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "小时候觉得大人什么都知道，长大后发现大人只是装作什么都知道。",
        "topics": ["成长", "人生", "感悟"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "放学后和朋友在巷子里踢球，球踢进了邻居家院子，谁也不敢去捡。那些朋友现在连微信都不怎么聊了。",
        "topics": ["童年", "友情", "回忆"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "第一次骑自行车摔了十几次，爸爸一直在后面扶着。后来才知道，他早就松手了。",
        "topics": ["童年", "父爱", "成长"],
        "modality": "text",
        "source": "user",
    },

    # 亲情与家庭
    {
        "text": "妈妈打电话来，问我吃了没。我说吃了。其实那天忘了吃午饭。不想让她担心。",
        "topics": ["亲情", "母亲", "独居"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "爸爸从不说想我，但每次我回家，桌上总有我爱吃的菜。",
        "topics": ["亲情", "父爱", "回家"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "奶奶记不清我的名字了，但还记得我爱吃她包的饺子。",
        "topics": ["亲情", "衰老", "记忆"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "给家里打电话，爸爸接的。说了几句就递给妈妈。男人之间的对话总是这么短。",
        "topics": ["亲情", "父子", "沟通"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "离家那天，妈妈在车站哭了。我头也不回地上了车，怕她看到我也在哭。",
        "topics": ["亲情", "离别", "成长"],
        "modality": "text",
        "source": "user",
    },

    # 职场与困惑
    {
        "text": "加班到凌晨两点，走出写字楼，发现整条街只有路灯和我。",
        "topics": ["职场", "加班", "孤独"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "开会时说了一堆，最后发现大家各说各的，什么也没决定。",
        "topics": ["职场", "会议", "效率"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "新来的实习生叫我老师。我愣了一下，才意识到自己已经不是新人了。",
        "topics": ["职场", "成长", "时间"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "离职那天，把工牌还给前台，突然觉得这张卡陪了我三年。",
        "topics": ["职场", "离职", "感慨"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "面试官问我的职业规划。我说了一堆，其实真正的规划是'活下去'。",
        "topics": ["职场", "面试", "现实"],
        "modality": "text",
        "source": "user",
    },

    # 爱情与亲密
    {
        "text": "分手那天没有争吵，只是她说'我们不合适'。我点了点头，好像早就知道。",
        "topics": ["爱情", "分手", "释然"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "翻到前任的朋友圈，她好像过得不错。我点了个赞，然后把手机放下。",
        "topics": ["爱情", "前任", "释然"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "收到前任的婚礼请柬。去还是不去？最后还是去了，带着一句'祝你幸福'。",
        "topics": ["爱情", "前任", "成长"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "恋爱时觉得每天都是情人节，分手后才知道每天都是普通日子。",
        "topics": ["爱情", "恋爱", "现实"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "相亲对象问我有什么要求。我说'聊得来就行'。心里想的是'像她那样的'。",
        "topics": ["爱情", "相亲", "过去"],
        "modality": "text",
        "source": "user",
    },

    # 城市与漂泊
    {
        "text": "在北京租房五年，搬了四次家。每次都以为是最后一次。",
        "topics": ["城市", "租房", "漂泊"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "地铁上看到一个女孩在哭，旁边的人都在看手机。我也在看手机。",
        "topics": ["城市", "地铁", "冷漠"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "周末在咖啡店坐了一下午，什么也没做。窗外的人行色匆匆，我突然觉得自己很奢侈。",
        "topics": ["城市", "独处", "奢侈"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "小区门口的便利店老板认识我了，每次都说'还是那个？'。这大概是我在这个城市最熟悉的人。",
        "topics": ["城市", "熟悉", "孤独"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "深夜加完班，走在回家路上，耳机里放着歌。突然觉得，这条路上只有我一个人。",
        "topics": ["城市", "深夜", "孤独"],
        "modality": "text",
        "source": "user",
    },

    # 自然与感悟
    {
        "text": "雨后的空气真好，有种洗过的感觉。深呼吸一口，好像把昨天的疲惫也呼出去了。",
        "topics": ["自然", "雨后", "放松"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "秋天的第一片落叶踩在脚下，发出清脆的声音。突然想起小时候踩落叶的快乐。",
        "topics": ["自然", "秋天", "回忆"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "今晚的月亮真圆。不知道远方的人，是不是也在看同一个月亮。",
        "topics": ["自然", "月亮", "思念"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "春天来了，小区的花都开了。每天路过都忍不住拍一张。生命真好。",
        "topics": ["自然", "春天", "生命"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "暴风雨来了，窗外的树被吹得东倒西歪。突然觉得，人也像树一样，要经得起风雨。",
        "topics": ["自然", "暴风雨", "人生"],
        "modality": "text",
        "source": "user",
    },

    # 阅读与思考
    {
        "text": "读完《百年孤独》，合上书，沉默了很久。有些故事，读完才知道自己有多幸运。",
        "topics": ["阅读", "百年孤独", "感悟"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "重读《小王子》，这次读懂了'驯服'的意思。原来建立关系，是需要付出时间的。",
        "topics": ["阅读", "小王子", "关系"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "读《月亮与六便士》，问自己：如果不用考虑钱，我最想做什么？答案让我沉默了。",
        "topics": ["阅读", "梦想", "现实"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "看完一部纪录片，讲的是深海里的鱼。它们在黑暗中发光，不知道有太阳这回事。突然觉得，人也一样。",
        "topics": ["阅读", "纪录片", "认知"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "读到一句话：'人的一切痛苦，本质上都是对自己无能的愤怒。'扎心了。",
        "topics": ["阅读", "金句", "反思"],
        "modality": "text",
        "source": "user",
    },

    # 音乐与情感
    {
        "text": "深夜戴上耳机，随机播放到一首老歌。旋律响起的瞬间，眼泪就下来了。不是因为歌好听，是因为想起了听这首歌时的自己。",
        "topics": ["音乐", "回忆", "情感"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "单曲循环了一整天的歌，终于知道为什么喜欢了。因为歌词写的就是我的故事。",
        "topics": ["音乐", "共鸣", "故事"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "在KTV里唱了一首《后来》，唱到'后来，我总算学会了如何去爱'，唱不下去了。",
        "topics": ["音乐", "后来", "遗憾"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "开车时听到电台放老歌，突然不想换台。让这首歌放完，就当是给过去的一个拥抱。",
        "topics": ["音乐", "老歌", "过去"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "弹吉他弹了十年，还是只会那几个和弦。但每次弹起《Tears in Heaven》，都会安静下来。",
        "topics": ["音乐", "吉他", "安静"],
        "modality": "text",
        "source": "user",
    },

    # 美食与生活
    {
        "text": "深夜煮了一碗泡面，加了个蛋。这大概是一天里最幸福的三分钟。",
        "topics": ["美食", "深夜", "简单"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "学会了妈妈的红烧肉做法，但总觉得少了点什么。后来明白了，少的是'妈妈做的'这四个字。",
        "topics": ["美食", "妈妈", "家"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "一个人去吃火锅，服务员问'几位？'我说一位。她愣了一下，我也愣了一下。",
        "topics": ["美食", "独食", "孤独"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "喝咖啡从不加糖，就像生活，苦习惯了就不觉得苦了。",
        "topics": ["美食", "咖啡", "生活"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "凌晨三点的便利店，买了一杯关东煮。店员说'慢走'，这是今天第一个人对我说的话。",
        "topics": ["美食", "便利店", "深夜"],
        "modality": "text",
        "source": "user",
    },

    # 旅行与见闻
    {
        "text": "一个人去了趟海边，坐在沙滩上看日落。海浪声很大，心里却很安静。",
        "topics": ["旅行", "海边", "独处"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "在古镇的小巷里迷路了，反而看到了最美的风景。人生大概也是这样。",
        "topics": ["旅行", "迷路", "人生"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "火车窗外的风景一直在变，车里的人大部分在睡觉。只有我在看窗外，假装在思考人生。",
        "topics": ["旅行", "火车", "思考"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "旅行回来，发现家里什么都没变。变的是我。",
        "topics": ["旅行", "归来", "改变"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "在异国他乡遇到一个中国人，聊了半小时。分别时说'有缘再见'，心里知道不会再见了。",
        "topics": ["旅行", "偶遇", "缘分"],
        "modality": "text",
        "source": "user",
    },

    # 社会观察
    {
        "text": "看到一个外卖小哥在雨中跑，突然觉得，每个人都在为生活奔跑。",
        "topics": ["社会", "外卖", "生活"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "地铁上，一个老人站着，周围的人都在看手机。我也在看手机。",
        "topics": ["社会", "地铁", "冷漠"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "看到新闻说某明星离婚了，评论区吵翻了天。我只想说，别人的婚姻，我们真的懂吗？",
        "topics": ["社会", "新闻", "思考"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "超市里看到一个妈妈在教孩子选水果，'要选这种，甜'。突然觉得，这就是传承。",
        "topics": ["社会", "传承", "生活"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "凌晨的医院走廊，有人在哭，有人在等。健康真好，活着真好。",
        "topics": ["社会", "医院", "生命"],
        "modality": "text",
        "source": "user",
    },

    # 科技与反思
    {
        "text": "手机内存又满了，删了几个App，突然发现，有些App删了就没再装回来。人也一样。",
        "topics": ["科技", "手机", "关系"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "AI写的诗比我好，画的画比我好。突然不知道，人还能做什么。",
        "topics": ["科技", "AI", "焦虑"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "给老同学发了条微信，显示'对方已开启好友验证'。原来，我已经不是他的好友了。",
        "topics": ["科技", "微信", "友情"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "智能推荐说我可能喜欢这首歌。它说对了，但我有点不舒服，被算法了解的感觉。",
        "topics": ["科技", "推荐", "隐私"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "云盘里的照片，有1万张。但真正想看的，只有那几张。",
        "topics": ["科技", "照片", "记忆"],
        "modality": "text",
        "source": "user",
    },

    # 深夜感慨
    {
        "text": "失眠了，盯着天花板。脑子里全是明天的事。但此刻，我只想安静地躺一会儿。",
        "topics": ["深夜", "失眠", "焦虑"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "凌晨四点醒来，窗外一片漆黑。突然觉得，世界好大，我好小。",
        "topics": ["深夜", "凌晨", "渺小"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "深夜删了一大段想发朋友圈的话，最后只发了个'晚安'。有些话，说给自己听就够了。",
        "topics": ["深夜", "朋友圈", "表达"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "夜里两点，收到一条'在吗'。回了个'在'。对方说'没事，就是睡不着'。原来，失眠的人不止我一个。",
        "topics": ["深夜", "失眠", "陪伴"],
        "modality": "text",
        "source": "user",
    },
    {
        "text": "深夜的出租车上，司机问我'今天过得怎么样'。我愣了一下，说'还行'。这是今天最温暖的一句话。",
        "topics": ["深夜", "出租车", "温暖"],
        "modality": "text",
        "source": "user",
    },
]


# ============================================================
# 工具函数
# ============================================================

def http_request(url, method="GET", data=None, headers=None):
    """HTTP 请求"""
    headers = headers or {}
    headers["Content-Type"] = "application/json"

    if data:
        data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.status
    except urllib.error.HTTPError as e:
        return {"error": str(e)}, e.code
    except Exception as e:
        return {"error": str(e)}, 0


def device_auth(device_fp):
    """设备认证，获取 token"""
    data = {
        "device_type": "phone",
        "device_fingerprint": device_fp,
        "os_version": "Android 14",
        "app_version": "0.3.0",
    }
    resp, status = http_request(f"{GATEWAY_URL}/auth/device", "POST", data)
    if status == 200 and "access_token" in resp:
        return resp["access_token"]
    return None


def create_anchor(token, fp, anchor_data):
    """创建锚点"""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Device-Fingerprint": fp,
    }
    data = {
        "modality": anchor_data.get("modality", "text"),
        "content_text": anchor_data.get("text"),
        "topics": anchor_data.get("topics", []),
        "source": anchor_data.get("source", "user"),
    }
    resp, status = http_request(
        f"{GATEWAY_URL}/anchors/import", "POST", data, headers
    )
    return resp, status


def submit_reaction(token, fp, anchor_id, reaction_type, emotion_word=None, text=None):
    """提交反应"""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Device-Fingerprint": fp,
    }
    data = {
        "anchor_id": anchor_id,
        "reaction_type": reaction_type,
        "modality": "text",
    }
    if emotion_word:
        data["emotion_word"] = emotion_word
    if text:
        data["text_content"] = text
    resp, status = http_request(
        f"{GATEWAY_URL}/reactions", "POST", data, headers
    )
    return resp, status


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("Standby 种子数据生成器 — 500 条真实感数据")
    print("=" * 60)

    # 1. 认证用户
    print("\n[1] 认证用户...")
    user_tokens = []
    for user in USERS:
        token = device_auth(user["device"])
        if token:
            user_tokens.append((user, token))
            print(f"  ✓ {user['name']} ({user['avatar']})")
        else:
            print(f"  ✗ {user['name']} 认证失败")

    if not user_tokens:
        print("\n没有可用的用户，退出")
        return

    # 2. 创建锚点
    print(f"\n[2] 创建锚点 ({len(ANCHORS)} 个)...")
    anchor_ids = []
    for i, anchor in enumerate(ANCHORS):
        user, token = random.choice(user_tokens)
        resp, status = create_anchor(token, user["device"], anchor)
        time.sleep(0.15)  # 速率限制
        
        if status == 200 and "anchor_id" in resp:
            anchor_ids.append(resp["anchor_id"])
            if (i + 1) % 10 == 0:
                print(f"  已创建 {i + 1}/{len(ANCHORS)} 个锚点")
        else:
            print(f"  ✗ 创建失败: {resp}")

    print(f"  ✓ 共创建 {len(anchor_ids)} 个锚点")

    # 3. 创建反应
    print(f"\n[3] 创建反应...")
    reaction_count = 0
    emotion_words = ["empathy", "trigger", "insight", "shock"]
    reaction_types = ["resonance", "neutral", "opposition", "unexperienced"]

    for anchor_id in anchor_ids:
        # 每个锚点 5-15 个反应
        num_reactions = random.randint(5, 15)
        for _ in range(num_reactions):
            user, token = random.choice(user_tokens)
            reaction_type = random.choices(
                reaction_types,
                weights=[0.4, 0.3, 0.1, 0.2],  # 共鸣最多
            )[0]
            emotion = random.choice(emotion_words) if reaction_type == "resonance" else None

            resp, status = submit_reaction(
                token, user["device"],
                anchor_id,
                reaction_type,
                emotion_word=emotion,
            )
            if status in [200, 201]:
                reaction_count += 1
                time.sleep(0.15)  # 速率限制

        if (len(anchor_ids) - anchor_ids.index(anchor_id)) % 10 == 0:
            print(f"  已处理 {len(anchor_ids) - anchor_ids.index(anchor_id)}/{len(anchor_ids)} 个锚点")

    print(f"  ✓ 共创建 {reaction_count} 个反应")

    # 4. 总结
    print("\n" + "=" * 60)
    print("种子数据生成完成!")
    print(f"  锚点: {len(anchor_ids)}")
    print(f"  反应: {reaction_count}")
    print(f"  用户: {len(user_tokens)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
