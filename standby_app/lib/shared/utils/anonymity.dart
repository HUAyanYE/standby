import 'dart:math';

class Anonymity {
  Anonymity._();

  static const _prefixes = [
    '夜的', '晨曦', '微风', '秋日', '冬雪', '春水', '夏雨', '远山',
    '近海', '深林', '浅滩', '孤星', '流云', '闲鹤', '静湖', '暖阳',
    '薄暮', '清露', '幽谷', '归鸟',
  ];

  static const _suffixes = [
    '旅人', '过客', '归人', '行者', '诗人', '歌者', '守望', '聆听',
    '沉思', '静默', '观察', '等待', '漂流', '停泊', '游荡', '栖息',
    '独白', '回响', '低语', '凝望',
  ];

  static const _avatars = [
    '🌙', '☀️', '🌊', '🍂', '🌸', '❄️', '🌿', '🍃', '☁️', '⭐',
    '🌻', '🍁', '🦋', '🐱', '🦊', '🐰', '🐻', '🐼', '🐨', '🦁',
    '🔮', '🎭', '🪶', '🌾', '🐚', '🫧', '🕯️', '📖', '🪨',
  ];

  static String nameFromId(String userId) {
    final hash = userId.hashCode.abs();
    return '${_prefixes[hash % _prefixes.length]}${_suffixes[(hash ~/ _prefixes.length) % _suffixes.length]}';
  }

  static String avatarFromId(String userId) {
    return _avatars[userId.hashCode.abs() % _avatars.length];
  }

  static final _random = Random();

  static String randomName() {
    return '${_prefixes[_random.nextInt(_prefixes.length)]}${_suffixes[_random.nextInt(_suffixes.length)]}';
  }

  static String randomAvatar() {
    return _avatars[_random.nextInt(_avatars.length)];
  }
}
