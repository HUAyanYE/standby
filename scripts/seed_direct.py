#!/usr/bin/env python3
"""
Standby 种子数据 — 直接写入数据库

绕过 BGE 编码（CPU 太慢），直接写入 PostgreSQL。
生成随机向量代替 BGE 编码。

用法: cd /mnt/d/Hermes/standby && python3 scripts/seed_direct.py
"""

import json
import random
import time
import uuid
import hashlib
import subprocess

# ============================================================
# 锚点数据
# ============================================================

ANCHORS = [
    ("小时候最喜欢下雨天，因为可以踩水坑。现在下雨天只想着别弄湿鞋。前天又下雨了，我撑着伞走在路上，看到一个小孩在踩水坑，突然很想脱了鞋也去踩。", ["童年", "成长", "下雨"]),
    ("整理旧物时翻到小学作文本，写的是'我的梦想是当科学家'。现在在写代码，也算某种意义上的科学家吧。只是这个科学家，经常加班到凌晨。", ["童年", "梦想", "成长"]),
    ("小时候觉得大人什么都知道，长大后发现大人只是装作什么都知道。现在我也在装了，面对后辈的问题，总是说'嗯，这个嘛...'。", ["成长", "人生", "感悟"]),
    ("放学后和朋友在巷子里踢球，球踢进了邻居家院子，谁也不敢去捡。那些朋友现在连微信都不怎么聊了。偶尔看到朋友圈，才知道他们也长大了。", ["童年", "友情", "回忆"]),
    ("第一次骑自行车摔了十几次，爸爸一直在后面扶着。后来才知道，他早就松手了。现在我也在学着松手，让孩子自己去摔。", ["童年", "父爱", "成长"]),
    ("妈妈打电话来，问我吃了没。我说吃了。其实那天忘了吃午饭，一直在改一个bug。不想让她担心，所以每次都说'吃了'。", ["亲情", "母亲", "独居"]),
    ("爸爸从不说想我，但每次我回家，桌上总有我爱吃的菜。走的时候，他会说'路上慢点'，然后转身进屋。我知道他在忍着不送我。", ["亲情", "父爱", "回家"]),
    ("奶奶记不清我的名字了，但还记得我爱吃她包的饺子。上次回去，她包了三种馅，说我爱吃韭菜的。我确实爱吃。", ["亲情", "衰老", "记忆"]),
    ("给家里打电话，爸爸接的。说了几句就递给妈妈。男人之间的对话总是这么短。但我知道，他一直在旁边听着。", ["亲情", "父子", "沟通"]),
    ("离家那天，妈妈在车站哭了。我头也不回地上了车，怕她看到我也在哭。后来她发了条微信：'到了报个平安'。", ["亲情", "离别", "成长"]),
    ("加班到凌晨两点，走出写字楼，发现整条街只有路灯和我。打了辆车，司机问我'这么晚下班啊'。我说'嗯'。其实我也不想这么晚。", ["职场", "加班", "孤独"]),
    ("开会时说了一堆，最后发现大家各说各的，什么也没决定。走出会议室，有人问'刚才说了啥'。我说'我也没听懂'。", ["职场", "会议", "效率"]),
    ("新来的实习生叫我老师。我愣了一下，才意识到自己已经不是新人了。时间过得真快，我还觉得自己是那个刚入职的新人。", ["职场", "成长", "时间"]),
    ("离职那天，把工牌还给前台，突然觉得这张卡陪了我三年。前台说'祝你前程似锦'。我说谢谢。其实也不知道前程在哪。", ["职场", "离职", "感慨"]),
    ("面试官问我的职业规划。我说了一堆，其实真正的规划是'活下去'。但他好像很满意我的回答。", ["职场", "面试", "现实"]),
    ("分手那天没有争吵，只是她说'我们不合适'。我点了点头，好像早就知道。后来才明白，'不合适'是最温柔的告别。", ["爱情", "分手", "释然"]),
    ("翻到前任的朋友圈，她好像过得不错。我点了个赞，然后把手机放下。有些人，放在心里就好。", ["爱情", "前任", "释然"]),
    ("收到前任的婚礼请柬。去还是不去？最后还是去了，带着一句'祝你幸福'。回家的路上，下了点小雨。", ["爱情", "前任", "成长"]),
    ("恋爱时觉得每天都是情人节，分手后才知道每天都是普通日子。但偶尔还是会想起，那些不普通的日子。", ["爱情", "恋爱", "现实"]),
    ("相亲对象问我有什么要求。我说'聊得来就行'。心里想的是'像她那样的'。但我没说。", ["爱情", "相亲", "过去"]),
    ("在北京租房五年，搬了四次家。每次都以为是最后一次。现在又在看房了。", ["城市", "租房", "漂泊"]),
    ("地铁上看到一个女孩在哭，旁边的人都在看手机。我也在看手机。但余光一直在看她。", ["城市", "地铁", "冷漠"]),
    ("周末在咖啡店坐了一下午，什么也没做。窗外的人行色匆匆，我突然觉得自己很奢侈。能什么都不做，也是一种幸福。", ["城市", "独处", "奢侈"]),
    ("小区门口的便利店老板认识我了，每次都说'还是那个？'。这大概是我在这个城市最熟悉的人。但我连他叫什么都不知道。", ["城市", "熟悉", "孤独"]),
    ("深夜加完班，走在回家路上，耳机里放着歌。突然觉得，这条路上只有我一个人。但有歌陪着，也还好。", ["城市", "深夜", "孤独"]),
    ("雨后的空气真好，有种洗过的感觉。深呼吸一口，好像把昨天的疲惫也呼出去了。明天又是新的一天。", ["自然", "雨后", "放松"]),
    ("秋天的第一片落叶踩在脚下，发出清脆的声音。突然想起小时候踩落叶的快乐。原来快乐可以这么简单。", ["自然", "秋天", "回忆"]),
    ("今晚的月亮真圆。不知道远方的人，是不是也在看同一个月亮。月亮不知道，但它把光给了所有人。", ["自然", "月亮", "思念"]),
    ("春天来了，小区的花都开了。每天路过都忍不住拍一张。生命真好，能看见这些花。", ["自然", "春天", "生命"]),
    ("暴风雨来了，窗外的树被吹得东倒西歪。突然觉得，人也像树一样，要经得起风雨。风雨过后，树还是树。", ["自然", "暴风雨", "人生"]),
    ("读完《百年孤独》，合上书，沉默了很久。有些故事，读完才知道自己有多幸运。孤独不可怕，可怕的是习惯了孤独。", ["阅读", "百年孤独", "感悟"]),
    ("重读《小王子》，这次读懂了'驯服'的意思。原来建立关系，是需要付出时间的。可惜我们都太忙了。", ["阅读", "小王子", "关系"]),
    ("读《月亮与六便士》，问自己：如果不用考虑钱，我最想做什么？答案让我沉默了。因为我真的不知道。", ["阅读", "梦想", "现实"]),
    ("看完一部纪录片，讲的是深海里的鱼。它们在黑暗中发光，不知道有太阳这回事。突然觉得，人也一样。有些光，要自己发。", ["阅读", "纪录片", "认知"]),
    ("读到一句话：'人的一切痛苦，本质上都是对自己无能的愤怒。'扎心了。但知道原因，也许就能治了。", ["阅读", "金句", "反思"]),
    ("深夜戴上耳机，随机播放到一首老歌。旋律响起的瞬间，眼泪就下来了。不是因为歌好听，是因为想起了听这首歌时的自己。", ["音乐", "回忆", "情感"]),
    ("单曲循环了一整天的歌，终于知道为什么喜欢了。因为歌词写的就是我的故事。有些歌，是写给深夜的。", ["音乐", "共鸣", "故事"]),
    ("在KTV里唱了一首《后来》，唱到'后来，我总算学会了如何去爱'，唱不下去了。后来的后来，我学会了沉默。", ["音乐", "后来", "遗憾"]),
    ("开车时听到电台放老歌，突然不想换台。让这首歌放完，就当是给过去的一个拥抱。", ["音乐", "老歌", "过去"]),
    ("弹吉他弹了十年，还是只会那几个和弦。但每次弹起《Tears in Heaven》，都会安静下来。有些歌，不需要弹得多好。", ["音乐", "吉他", "安静"]),
    ("深夜煮了一碗泡面，加了个蛋。这大概是一天里最幸福的三分钟。吃完继续加班。", ["美食", "深夜", "简单"]),
    ("学会了妈妈的红烧肉做法，但总觉得少了点什么。后来明白了，少的是'妈妈做的'这四个字。", ["美食", "妈妈", "家"]),
    ("一个人去吃火锅，服务员问'几位？'我说一位。她愣了一下，我也愣了一下。但火锅还是很好吃。", ["美食", "独食", "孤独"]),
    ("喝咖啡从不加糖，就像生活，苦习惯了就不觉得苦了。但偶尔加一次糖，会觉得特别甜。", ["美食", "咖啡", "生活"]),
    ("凌晨三点的便利店，买了一杯关东煮。店员说'慢走'，这是今天第一个人对我说的话。突然觉得便利店很温暖。", ["美食", "便利店", "深夜"]),
    ("一个人去了趟海边，坐在沙滩上看日落。海浪声很大，心里却很安静。有些声音，是用来安静的。", ["旅行", "海边", "独处"]),
    ("在古镇的小巷里迷路了，反而看到了最美的风景。人生大概也是这样，迷路有时候是找到路的开始。", ["旅行", "迷路", "人生"]),
    ("火车窗外的风景一直在变，车里的人大部分在睡觉。只有我在看窗外，假装在思考人生。其实在发呆。", ["旅行", "火车", "思考"]),
    ("旅行回来，发现家里什么都没变。变的是我。原来旅行的意义不是看风景，是看自己。", ["旅行", "归来", "改变"]),
    ("在异国他乡遇到一个中国人，聊了半小时。分别时说'有缘再见'，心里知道不会再见了。但那半小时，很温暖。", ["旅行", "偶遇", "缘分"]),
    ("看到一个外卖小哥在雨中跑，突然觉得，每个人都在为生活奔跑。我也是。", ["社会", "外卖", "生活"]),
    ("地铁上，一个老人站着，周围的人都在看手机。我也在看手机。但后来我站起来了。", ["社会", "地铁", "冷漠"]),
    ("看到新闻说某明星离婚了，评论区吵翻了天。我只想说，别人的婚姻，我们真的懂吗？", ["社会", "新闻", "思考"]),
    ("超市里看到一个妈妈在教孩子选水果，'要选这种，甜'。突然觉得，这就是传承。有些东西，课本里学不到。", ["社会", "传承", "生活"]),
    ("凌晨的医院走廊，有人在哭，有人在等。健康真好，活着真好。突然觉得，其他都是小事。", ["社会", "医院", "生命"]),
    ("手机内存又满了，删了几个App，突然发现，有些App删了就没再装回来。人也一样。", ["科技", "手机", "关系"]),
    ("AI写的诗比我好，画的画比我好。突然不知道，人还能做什么。但AI不会在深夜哭，所以还是人厉害。", ["科技", "AI", "焦虑"]),
    ("给老同学发了条微信，显示'对方已开启好友验证'。原来，我已经不是他的好友了。但没关系，我也没加回去。", ["科技", "微信", "友情"]),
    ("智能推荐说我可能喜欢这首歌。它说对了，但我有点不舒服，被算法了解的感觉。人不想被看透，哪怕被机器。", ["科技", "推荐", "隐私"]),
    ("云盘里的照片，有1万张。但真正想看的，只有那几张。其他的，只是证明我活过。", ["科技", "照片", "记忆"]),
    ("失眠了，盯着天花板。脑子里全是明天的事。但此刻，我只想安静地躺一会儿。明天的事，明天再说。", ["深夜", "失眠", "焦虑"]),
    ("凌晨四点醒来，窗外一片漆黑。突然觉得，世界好大，我好小。但这个小小的我，也在努力活着。", ["深夜", "凌晨", "渺小"]),
    ("深夜删了一大段想发朋友圈的话，最后只发了个'晚安'。有些话，说给自己听就够了。", ["深夜", "朋友圈", "表达"]),
    ("夜里两点，收到一条'在吗'。回了个'在'。对方说'没事，就是睡不着'。原来，失眠的人不止我一个。但能互相陪着，也好。", ["深夜", "失眠", "陪伴"]),
    ("深夜的出租车上，司机问我'今天过得怎么样'。我愣了一下，说'还行'。这是今天最温暖的一句话。有时候，陌生人比熟人更暖。", ["深夜", "出租车", "温暖"]),
]

# ============================================================
# 用户数据
# ============================================================

USERS = [
    {"name": "夜的旅人", "avatar": "🌙", "device": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"},
    {"name": "晨曦行者", "avatar": "☀️", "device": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3"},
    {"name": "微风诗人", "avatar": "🌊", "device": "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"},
    {"name": "秋日守望", "avatar": "🍂", "device": "d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5"},
    {"name": "冬雪归人", "avatar": "❄️", "device": "e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"},
]

# ============================================================
# 直接写入数据库
# ============================================================

def run_sql(sql, params=None):
    """执行 SQL"""
    if params:
        # 转义参数
        escaped = sql
        for p in params:
            if isinstance(p, str):
                p = p.replace("'", "''")
                escaped = escaped.replace("%s", f"'{p}'", 1)
            elif isinstance(p, list):
                p_str = json.dumps(p).replace("'", "''")
                escaped = escaped.replace("%s", f"'{p_str}'", 1)
            elif p is None:
                escaped = escaped.replace("%s", "NULL", 1)
            else:
                escaped = escaped.replace("%s", str(p), 1)
        cmd = f'docker exec standby-postgres psql -U standby -d standby -c "{escaped}"'
    else:
        cmd = f'docker exec standby-postgres psql -U standby -d standby -c "{sql}"'

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return result.stdout, result.returncode


def main():
    print("=" * 60)
    print("Standby 种子数据 — 直接写入数据库")
    print("=" * 60)

    # 1. 创建用户
    print("\n[1] 创建用户...")
    for user in USERS:
        user_id = hashlib.sha256(user["device"].encode()).hexdigest()[:16]
        phone_hash = hashlib.sha256(user["name"].encode()).hexdigest()
        token = hashlib.sha256(f"{user['name']}_{user['device']}".encode()).hexdigest()

        sql = f"""INSERT INTO users (id, phone_hash, internal_token, device_fingerprint, credit_score, marker_credit)
            VALUES ('{user_id}', '{phone_hash}', '{token}', '{user['device']}', 0.5, 0.5)
            ON CONFLICT (phone_hash) DO NOTHING"""
        out, code = run_sql(sql)
        if code == 0:
            print(f"  ✓ {user['name']} ({user['avatar']})")
        else:
            print(f"  ✗ {user['name']}: {out[:100]}")

    # 2. 创建锚点
    print(f"\n[2] 创建锚点 ({len(ANCHORS)} 个)...")
    anchor_ids = []
    for i, (text, topics) in enumerate(ANCHORS):
        anchor_id = f"a_{hashlib.sha256(text.encode()).hexdigest()[:8]}"
        user = random.choice(USERS)
        user_id = hashlib.sha256(user["device"].encode()).hexdigest()[:16]
        topics_json = json.dumps(topics).replace("'", "''")

        # 生成随机向量 (代替 BGE 编码)
        vector = [round(random.uniform(-0.1, 0.1), 6) for _ in range(768)]
        vector_str = str(vector).replace("'", "")

        sql = f"""INSERT INTO anchors (id, creator_id, modality, text_content, topics, source, quality_score)
            VALUES ('{anchor_id}', '{user_id}', 'text', '{text.replace(chr(39), chr(39)+chr(39))}', '{topics_json}', 'user', {round(random.uniform(0.3, 0.5), 2)})
            ON CONFLICT (id) DO NOTHING"""
        out, code = run_sql(sql)

        # 也写入 anchor_vectors
        sql2 = f"""INSERT INTO anchor_vectors (anchor_id, vector)
            VALUES ('{anchor_id}', '{vector_str}'::vector)
            ON CONFLICT (anchor_id) DO NOTHING"""
        run_sql(sql2)

        if code == 0:
            anchor_ids.append(anchor_id)

        if (i + 1) % 10 == 0:
            print(f"  已创建 {i + 1}/{len(ANCHORS)} 个锚点")

    print(f"  ✓ 共创建 {len(anchor_ids)} 个锚点")

    # 3. 创建反应
    print(f"\n[3] 创建反应...")
    reaction_count = 0
    emotion_words = ["empathy", "trigger", "insight", "shock"]
    reaction_types = ["resonance", "neutral", "opposition", "unexperienced"]

    for anchor_id in anchor_ids:
        num_reactions = random.randint(5, 15)
        for _ in range(num_reactions):
            user = random.choice(USERS)
            user_id = hashlib.sha256(user["device"].encode()).hexdigest()[:16]
            reaction_type = random.choices(
                reaction_types,
                weights=[0.4, 0.3, 0.1, 0.2],
            )[0]
            emotion = random.choice(emotion_words) if reaction_type == "resonance" else None

            reaction_id = f"r_{uuid.uuid4().hex[:12]}"
            emotion_val = f"'{emotion}'" if emotion else "NULL"
            text = random.choice([
                "我也经历过类似的事情",
                "这让我想起了...",
                "说出了我想说的话",
                "突然被触动了",
                "原来不止我一个人这样",
            ]).replace("'", "''")

            sql = f"""INSERT INTO reactions (id, user_id, anchor_id, reaction_type, emotion_word, modality, text_content, resonance_value)
                VALUES ('{reaction_id}', '{user_id}', '{anchor_id}', '{reaction_type}', {emotion_val}, 'text', '{text}', {round(random.uniform(0.3, 0.9), 3)})"""
            out, code = run_sql(sql)
            if code == 0:
                reaction_count += 1

    print(f"  ✓ 共创建 {reaction_count} 个反应")

    # 4. 创建关系
    print(f"\n[4] 创建关系...")
    rel_count = 0
    for i in range(len(USERS)):
        for j in range(i + 1, len(USERS)):
            user_a = hashlib.sha256(USERS[i]["device"].encode()).hexdigest()[:16]
            user_b = hashlib.sha256(USERS[j]["device"].encode()).hexdigest()[:16]
            score = round(random.uniform(0.1, 0.8), 3)

            sql = f"""INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a, trust_level)
                VALUES ('{user_a}', '{user_b}', {score}, {score}, {random.randint(0, 3)})
                ON CONFLICT (user_a_hash, user_b_hash) DO NOTHING"""
            out, code = run_sql(sql)
            if code == 0:
                rel_count += 1

    print(f"  ✓ 共创建 {rel_count} 个关系")

    # 5. 总结
    print("\n" + "=" * 60)
    print("种子数据生成完成!")
    print(f"  用户: {len(USERS)}")
    print(f"  锚点: {len(anchor_ids)}")
    print(f"  反应: {reaction_count}")
    print(f"  关系: {rel_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
