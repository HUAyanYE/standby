import 'dart:math';

/// 昵称生成器 — 多风格词库组合
class NicknameGenerator {
  static final _random = Random();

  // ── 风格一：自然意象 ──────────────────────────────────────────
  static const _naturePrefixes = [
    '夜的', '晨曦', '微风', '秋日', '冬雪', '春水', '夏雨',
    '远山', '近海', '深林', '浅滩', '孤星', '流云', '闲鹤',
    '静湖', '暖阳', '清泉', '古木', '新月', '落花', '飞鸟',
    '薄雾', '斜阳', '细雨', '长风', '幽兰', '寒梅', '青竹',
  ];

  static const _natureSuffixes = [
    '旅人', '过客', '归人', '行者', '渔夫', '樵夫', '耕者',
    '诗人', '画家', '歌者', '守望', '聆听', '沉思', '静默',
    '观察', '等待', '漂流', '停泊', '游荡', '栖息', '驻足',
    '踱步', '凝望', '回响', '呢喃', '低语', '独酌', '漫步',
  ];

  // ── 风格二：时间与季节 ──────────────────────────────────────────
  static const _timePrefixes = [
    '黎明', '黄昏', '深夜', '午后', '清晨', '傍晚',
    '春天', '夏天', '秋天', '冬天', '四季', '经年',
    '昨日', '今朝', '往昔', '此刻', '当时', '未来',
  ];

  static const _timeSuffixes = [
    '故事', '记忆', '思念', '等待', '守候', '期盼',
    '回响', '痕迹', '光影', '温度', '气息', '声音',
    '梦', '歌', '诗', '雨', '风', '雪',
  ];

  // ── 风格三：情绪与感受 ──────────────────────────────────────────
  static const _emotionPrefixes = [
    '安静', '温柔', '沉默', '孤独', '自由', '平静',
    '微凉', '温暖', '淡然', '从容', '简单', '真实',
    '坦然', '释然', '随缘', '知足', '感恩', '珍惜',
  ];

  static const _emotionSuffixes = [
    '的人', '的心', '的灵魂', '的影子', '的声音', '的角落',
    '的角落', '的夜晚', '的清晨', '的瞬间', '的时光', '的自己',
    '者', '客', '人', '心',
  ];

  // ── 风格四：诗意表达 ──────────────────────────────────────────
  static const _poeticNames = [
    '月下独酌', '风中追风', '雨中漫步', '雪夜归人',
    '山间明月', '江上清风', '林间小道', '海边拾贝',
    '云端旅人', '星河守望', '时光旅者', '梦境编织',
    '静水深流', '落叶知秋', '春风化雨', '冬日暖阳',
    '半山听雨', '临窗听雪', '凭栏望月', '踏雪寻梅',
    '闲看花开', '静待花落', '淡看云起', '细听风吟',
  ];

  // ── 风格五：Emoji + 文字组合 ──────────────────────────────────────────
  static const _emojiPrefixes = [
    '🌙', '☀️', '🌊', '🍂', '🌸', '❄️', '🌿', '🍃',
    '☁️', '⭐', '🌻', '🍁', '🌺', '🌴', '🌵', '🌲',
    '🦋', '🐦', '🐱', '🦊', '🐰', '🐻', '🐼', '🦁',
    '🌙', '💫', '✨', '🌟', '💎', '🔮', '🪐', '🌍',
  ];

  static const _emojiSuffixes = [
    '的旅人', '的守望', '的聆听', '的沉思', '的等待',
    '的归人', '的行者', '的诗人', '的画家', '的歌者',
    '小站', '角落', '日记', '时光', '故事', '梦境',
    '漫游', '漂流', '漫步', '探险', '旅行', '冒险',
  ];

  /// 生成一个随机昵称
  static String generate() {
    final style = _random.nextInt(5);
    switch (style) {
      case 0:
        return _generateNature();
      case 1:
        return _generateTime();
      case 2:
        return _generateEmotion();
      case 3:
        return _generatePoetic();
      case 4:
        return _generateEmoji();
      default:
        return _generateNature();
    }
  }

  /// 生成一批昵称（3个）
  static List<String> generateBatch() {
    final names = <String>{};
    while (names.length < 3) {
      names.add(generate());
    }
    return names.toList();
  }

  // ── 各风格生成方法 ──────────────────────────────────────────

  static String _generateNature() {
    final prefix = _naturePrefixes[_random.nextInt(_naturePrefixes.length)];
    final suffix = _natureSuffixes[_random.nextInt(_natureSuffixes.length)];
    return '$prefix$suffix';
  }

  static String _generateTime() {
    final prefix = _timePrefixes[_random.nextInt(_timePrefixes.length)];
    final suffix = _timeSuffixes[_random.nextInt(_timeSuffixes.length)];
    return '$prefix$suffix';
  }

  static String _generateEmotion() {
    final prefix = _emotionPrefixes[_random.nextInt(_emotionPrefixes.length)];
    final suffix = _emotionSuffixes[_random.nextInt(_emotionSuffixes.length)];
    return '$prefix$suffix';
  }

  static String _generatePoetic() {
    return _poeticNames[_random.nextInt(_poeticNames.length)];
  }

  static String _generateEmoji() {
    final prefix = _emojiPrefixes[_random.nextInt(_emojiPrefixes.length)];
    final suffix = _emojiSuffixes[_random.nextInt(_emojiSuffixes.length)];
    return '$prefix$suffix';
  }
}
