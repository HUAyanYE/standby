import 'package:flutter/material.dart';
import '../services/storage_service.dart';
import '../models/user_identity.dart';
import '../constants/app_constants.dart';

/// 我页 — 设置 + 数据统计
class MeScreen extends StatefulWidget {
  final UserIdentity userIdentity;

  const MeScreen({super.key, required this.userIdentity});

  @override
  State<MeScreen> createState() => _MeScreenState();
}

class _MeScreenState extends State<MeScreen> {
  final _storage = StorageService();
  late String _swipeDirection;
  late UserIdentity _currentIdentity;

  @override
  void initState() {
    super.initState();
    _swipeDirection = _storage.swipeDirection;
    _currentIdentity = widget.userIdentity;
  }

  void _showSwipeDirectionDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('锚点滑动方式'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            RadioListTile<String>(
              title: const Text('上下滑动'),
              value: 'vertical',
              groupValue: _swipeDirection,
              onChanged: (value) {
                _storage.setSwipeDirection(value!);
                setState(() => _swipeDirection = value);
                Navigator.pop(context);
              },
            ),
            RadioListTile<String>(
              title: const Text('左右滑动'),
              value: 'horizontal',
              groupValue: _swipeDirection,
              onChanged: (value) {
                _storage.setSwipeDirection(value!);
                setState(() => _swipeDirection = value);
                Navigator.pop(context);
              },
            ),
          ],
        ),
      ),
    );
  }

  void _editIdentity() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _EditIdentitySheet(
        currentNickname: _currentIdentity.nickname,
        currentAvatar: _currentIdentity.avatar,
        onSave: (nickname, avatar) async {
          // 保存新身份
          final newIdentity = UserIdentity(nickname: nickname, avatar: avatar);
          await _storage.setUserIdentity(newIdentity.toJson());
          setState(() => _currentIdentity = newIdentity);
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final reactions = _storage.myReactions;
    final totalResonance = reactions.where((r) => r['reaction_type'] == '共鸣').length;
    final uniqueAnchors = reactions.map((r) => r['anchor_id']).toSet().length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('我'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // 身份卡片（可点击编辑）
            GestureDetector(
              onTap: _editIdentity,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.indigo.shade50,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Column(
                  children: [
                    Text(
                      _currentIdentity.avatar,
                      style: const TextStyle(fontSize: 48),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _currentIdentity.nickname,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.edit,
                          size: 14,
                          color: Colors.grey.shade500,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '点击编辑',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade500,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // 我的数据
            _buildSection(
              title: '📊 我的数据',
              children: [
                _buildDataRow('共鸣次数', '$totalResonance 次'),
                _buildDataRow('参与锚点', '$uniqueAnchors 个'),
                _buildDataRow('写下观点', '${reactions.where((r) => r['emotion_word'] != null).length} 条'),
                _buildDataRow('知己', '0 人'),
              ],
            ),
            const SizedBox(height: 16),

            // 偏好设置
            _buildSection(
              title: '⚙️ 偏好设置',
              children: [
                _buildSettingRow(
                  icon: Icons.swap_vert,
                  title: '锚点滑动方式',
                  value: _swipeDirection == 'vertical' ? '上下滑动' : '左右滑动',
                  onTap: _showSwipeDirectionDialog,
                ),
                _buildSettingRow(
                  icon: Icons.brightness_6_outlined,
                  title: '外观模式',
                  value: '跟随系统',
                  onTap: () {
                    // TODO: 主题切换
                  },
                ),
              ],
            ),
            const SizedBox(height: 16),

            // 关于
            _buildSection(
              title: 'ℹ️ 关于',
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      // Logo 和名称
                      Container(
                        width: 64,
                        height: 64,
                        decoration: BoxDecoration(
                          color: Colors.indigo.shade50,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: const Center(
                          child: Text(
                            '📖',
                            style: TextStyle(fontSize: 32),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        AppConstants.appName,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'v${AppConstants.appVersion}',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey.shade500,
                        ),
                      ),
                      const SizedBox(height: 16),
                      // 描述
                      Text(
                        '有共鸣才有真实感想',
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.grey.shade700,
                          fontWeight: FontWeight.w500,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '在 Standby，每一次共鸣都是真实的表达。\n我们相信，真正的想法来自于共同的体验。',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey.shade500,
                          height: 1.5,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      // 特性
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _buildFeatureItem('🔒', '隐私保护'),
                          _buildFeatureItem('💭', '真实共鸣'),
                          _buildFeatureItem('🌍', '匿名交流'),
                        ],
                      ),
                      const SizedBox(height: 16),
                      // 版本信息
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.grey.shade100,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          'Build ${AppConstants.buildNumber}',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection({required String title, required List<Widget> children}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Text(
              title,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade600,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          ...children,
        ],
      ),
    );
  }

  Widget _buildDataRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 14)),
          Text(
            value,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey.shade600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSettingRow({
    required IconData icon,
    required String title,
    required String value,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Icon(icon, size: 20, color: Colors.grey.shade600),
            const SizedBox(width: 12),
            Expanded(
              child: Text(title, style: const TextStyle(fontSize: 14)),
            ),
            Text(
              value,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade500,
              ),
            ),
            const SizedBox(width: 8),
            Icon(Icons.chevron_right, size: 20, color: Colors.grey.shade400),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureItem(String emoji, String label) {
    return Column(
      children: [
        Text(
          emoji,
          style: const TextStyle(fontSize: 24),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
          ),
        ),
      ],
    );
  }
}

/// 编辑身份的底部弹窗
class _EditIdentitySheet extends StatefulWidget {
  final String currentNickname;
  final String currentAvatar;
  final Function(String nickname, String avatar) onSave;

  const _EditIdentitySheet({
    required this.currentNickname,
    required this.currentAvatar,
    required this.onSave,
  });

  @override
  State<_EditIdentitySheet> createState() => _EditIdentitySheetState();
}

class _EditIdentitySheetState extends State<_EditIdentitySheet> {
  late TextEditingController _nicknameController;
  late TextEditingController _avatarController;

  @override
  void initState() {
    super.initState();
    _nicknameController = TextEditingController(text: widget.currentNickname);
    _avatarController = TextEditingController(text: widget.currentAvatar);
  }

  @override
  void dispose() {
    _nicknameController.dispose();
    _avatarController.dispose();
    super.dispose();
  }

  void _save() {
    final nickname = _nicknameController.text.trim();
    final avatar = _avatarController.text.trim();

    if (nickname.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('昵称不能为空'), backgroundColor: Colors.red),
      );
      return;
    }

    if (avatar.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('头像不能为空'), backgroundColor: Colors.red),
      );
      return;
    }

    widget.onSave(nickname, avatar);
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 24,
        right: 24,
        top: 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 标题
          const Text(
            '编辑身份',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),

          // 头像预览
          Text(
            _avatarController.text,
            style: const TextStyle(fontSize: 48),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),

          // 头像输入
          TextField(
            controller: _avatarController,
            decoration: InputDecoration(
              labelText: '头像',
              hintText: '输入任意 emoji',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 16),

          // 昵称输入
          TextField(
            controller: _nicknameController,
            decoration: InputDecoration(
              labelText: '昵称',
              hintText: '输入你的昵称',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
          const SizedBox(height: 24),

          // 保存按钮
          ElevatedButton(
            onPressed: _save,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.indigo,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: const Text(
              '保存',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}
