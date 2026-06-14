class Formatters {
  Formatters._();

  static String formatTime(int timestamp) {
    final ts = timestamp > 1e12 ? timestamp : timestamp * 1000;
    final date = DateTime.fromMillisecondsSinceEpoch(ts);
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inMinutes < 1) return '刚刚';
    if (diff.inHours < 1) return '${diff.inMinutes}分钟前';
    if (diff.inDays < 1) return '${diff.inHours}小时前';
    if (diff.inDays < 30) return '${diff.inDays}天前';
    return '${date.month}月${date.day}日';
  }

  static String formatDate(int timestamp) {
    final date = DateTime.fromMillisecondsSinceEpoch(timestamp);
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final dateOnly = DateTime(date.year, date.month, date.day);

    if (dateOnly == today) return '今天';
    if (dateOnly == yesterday) return '昨天';
    return '${date.month}月${date.day}日';
  }

  static const emotionWords = {
    1: '同感',
    2: '触发',
    3: '启发',
    4: '震撼',
  };

  static String? emotionWordLabel(dynamic value) {
    if (value == null) return null;
    final v = value is int ? value : int.tryParse(value.toString());
    return emotionWords[v];
  }
}
