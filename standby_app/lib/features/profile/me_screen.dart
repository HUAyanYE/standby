import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../shared/services/storage_service.dart';
import '../../shared/models/user_identity.dart';
import '../../shared/providers/feature_unlock_provider.dart';
import '../../core/constants/app_constants.dart';
import '../../app/theme.dart';
import '../../app/theme_colors.dart';
import '../../app/theme_provider.dart';

/// 我页 — 个人信息、设置、知己入口
class MeScreen extends ConsumerStatefulWidget {
  const MeScreen({super.key});

  @override
  ConsumerState<MeScreen> createState() => _MeScreenState();
}

class _MeScreenState extends ConsumerState<MeScreen> {
  final _storage = StorageService();
  late UserIdentity _currentIdentity;

  @override
  void initState() {
    super.initState();
    final identityData = _storage.userIdentity;
    _currentIdentity = identityData != null
        ? UserIdentity.fromJson(identityData)
        : UserIdentity(deviceId: '', setNickname: '旅人', setAvatar: '🌙');
  }

  void _editIdentity() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: context.surface1,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(StandbyRadius.xl)),
      ),
      builder: (context) => _EditIdentitySheet(
        currentNickname: _currentIdentity.nickname,
        currentAvatar: _currentIdentity.avatar,
        onSave: (nickname, avatar) async {
          final newIdentity = UserIdentity(
            deviceId: _currentIdentity.deviceId,
            setNickname: nickname,
            setAvatar: avatar,
          );
          await _storage.setUserIdentity(newIdentity.toJson());
          setState(() => _currentIdentity = newIdentity);
        },
      ),
    );
  }

  String _themeModeLabel(AppThemeMode mode) {
    switch (mode) {
      case AppThemeMode.dark:
        return '暗色';
      case AppThemeMode.light:
        return '亮色';
      case AppThemeMode.system:
        return '跟随系统';
    }
  }

  void _showThemePicker(BuildContext context, WidgetRef ref) {
    final current = ref.read(themeModeProvider);
    showModalBottomSheet(
      context: context,
      backgroundColor: context.surface1,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(StandbyRadius.xl)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('外观模式', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: context.textColor)),
            const SizedBox(height: 20),
            ...AppThemeMode.values.map((mode) {
              final selected = mode == current;
              return ListTile(
                key: Key('theme_${mode.name}'),
                leading: Icon(
                  mode == AppThemeMode.dark
                      ? Icons.dark_mode_outlined
                      : mode == AppThemeMode.light
                          ? Icons.light_mode_outlined
                          : Icons.brightness_auto_outlined,
                  color: selected ? StandbyColors.primary : context.text2Color,
                ),
                title: Text(
                  _themeModeLabel(mode),
                  style: TextStyle(
                    color: selected ? StandbyColors.primary : context.textColor,
                    fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
                  ),
                ),
                trailing: selected ? const Icon(Icons.check, color: StandbyColors.primary) : null,
                onTap: () {
                  ref.read(themeModeProvider.notifier).setMode(mode);
                  Navigator.pop(ctx);
                },
              );
            }),
          ],
        ),
      ),
    );
  }

  String _getResonanceDescription() {
    final reactions = _storage.myReactions;
    final resonanceCount = reactions.where((r) => r['reaction_type'] == '共鸣').length;
    if (resonanceCount == 0) return '还没有共鸣记录';
    if (resonanceCount < 5) return '刚刚开始感受世界';
    if (resonanceCount < 20) return '正在积累共鸣的深度';
    return '已有丰富的共鸣体验';
  }

  String _getExpressionDescription() {
    final posts = _storage.myPosts;
    if (posts.isEmpty) return '还没有发布内容';
    if (posts.length < 5) return '开始了表达的旅程';
    if (posts.length < 20) return '持续记录着感受';
    return '表达已成为习惯';
  }

  @override
  Widget build(BuildContext context) {
    final confidantUnlocked = ref.watch(featureUnlockProvider(FeatureType.confidantChat));

    return Scaffold(
      appBar: AppBar(title: const Text('我')),
      body: SingleChildScrollView(
        padding: StandbySpacing.pagePadding,
        child: Column(
          children: [
            // 身份卡片
            GestureDetector(
              onTap: _editIdentity,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: context.surface1,
                  borderRadius: StandbyRadius.cardRadius,
                  border: Border.all(color: context.borderColor),
                ),
                child: Column(
                  children: [
                    Text(_currentIdentity.avatar, style: const TextStyle(fontSize: 48)),
                    const SizedBox(height: 12),
                    Text(
                      _currentIdentity.nickname,
                      style: StandbyTextStyles.h2,
                    ),
                    const SizedBox(height: 4),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.edit, size: 14, color: context.text3Color),
                        const SizedBox(width: 4),
                        Text('点击编辑', style: TextStyle(fontSize: 12, color: context.text3Color)),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // 感受轨迹
            _buildSection(
              title: '📖 感受轨迹',
              children: [
                _buildQualitativeRow(icon: Icons.favorite_outline, text: _getResonanceDescription()),
                _buildQualitativeRow(icon: Icons.edit_note, text: _getExpressionDescription()),
              ],
            ),
            const SizedBox(height: 16),

            // 知己入口（渐进解锁）
            if (confidantUnlocked) ...[
              _buildSection(
                title: '🕯 知己',
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      children: [
                        const Text('🕯', style: TextStyle(fontSize: 32)),
                        const SizedBox(height: 8),
                        Text('知己', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: context.textColor)),
                        const SizedBox(height: 8),
                        Text('暂时无人', style: TextStyle(fontSize: 14, color: context.text2Color)),
                        const SizedBox(height: 4),
                        Text('共鸣需要时间沉淀', style: TextStyle(fontSize: 12, color: context.text3Color)),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: () => context.push('/confidant'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: StandbyColors.primary,
                            foregroundColor: Colors.white,
                          ),
                          child: const Text('查看知己'),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
            ],

            // 偏好设置
            _buildSection(
              title: '⚙️ 偏好设置',
              children: [
                _buildSettingRow(
                  icon: Icons.brightness_6_outlined,
                  title: '外观模式',
                  value: _themeModeLabel(ref.watch(themeModeProvider)),
                  onTap: () => _showThemePicker(context, ref),
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
                      Container(
                        width: 64,
                        height: 64,
                        decoration: BoxDecoration(
                          color: context.surface2,
                          borderRadius: BorderRadius.circular(StandbyRadius.lg),
                        ),
                        child: const Center(child: Text('📖', style: TextStyle(fontSize: 32))),
                      ),
                      const SizedBox(height: 12),
                      Text(AppConstants.appName, style: StandbyTextStyles.h2),
                      const SizedBox(height: 4),
                      Text('v${AppConstants.appVersion}', style: TextStyle(fontSize: 14, color: context.text3Color)),
                      const SizedBox(height: 16),
                      Text(
                        '有共鸣才有真实感想',
                        style: TextStyle(fontSize: 16, color: context.text2Color, fontWeight: FontWeight.w500),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '在 Standby，每一次共鸣都是真实的表达。\n我们相信，真正的想法来自于共同的体验。',
                        style: TextStyle(fontSize: 14, color: context.text3Color, height: 1.5),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _buildFeatureItem('🔒', '隐私保护'),
                          _buildFeatureItem('💭', '真实共鸣'),
                          _buildFeatureItem('🌍', '匿名交流'),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: context.surface2,
                          borderRadius: BorderRadius.circular(StandbyRadius.sm),
                        ),
                        child: Text(
                          'Build ${AppConstants.buildNumber}',
                          style: TextStyle(fontSize: 12, color: context.text3Color),
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
        color: context.surface1,
        borderRadius: StandbyRadius.cardRadius,
        border: Border.all(color: context.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Text(title, style: TextStyle(fontSize: 14, color: context.text2Color, fontWeight: FontWeight.w500)),
          ),
          ...children,
        ],
      ),
    );
  }

  Widget _buildQualitativeRow({required IconData icon, required String text}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          Icon(icon, size: 18, color: context.text2Color),
          const SizedBox(width: 12),
          Expanded(child: Text(text, style: TextStyle(fontSize: 14, color: context.textColor))),
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
            Icon(icon, size: 20, color: context.text2Color),
            const SizedBox(width: 12),
            Expanded(child: Text(title, style: TextStyle(fontSize: 14, color: context.textColor))),
            Text(value, style: TextStyle(fontSize: 14, color: context.text3Color)),
            const SizedBox(width: 8),
            Icon(Icons.chevron_right, size: 20, color: context.text3Color),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureItem(String emoji, String label) {
    return Column(
      children: [
        Text(emoji, style: const TextStyle(fontSize: 24)),
        const SizedBox(height: 4),
        Text(label, style: TextStyle(fontSize: 12, color: context.text2Color)),
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
        const SnackBar(content: Text('昵称不能为空'), backgroundColor: StandbyColors.primary),
      );
      return;
    }

    if (avatar.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('头像不能为空'), backgroundColor: StandbyColors.primary),
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
        left: 24, right: 24, top: 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('编辑身份', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: context.textColor), textAlign: TextAlign.center),
          const SizedBox(height: 24),
          TextField(
            controller: _avatarController,
            style: const TextStyle(fontSize: 32),
            textAlign: TextAlign.center,
            decoration: InputDecoration(
              hintText: '选择一个 Emoji',
              hintStyle: TextStyle(color: context.text3Color),
              border: OutlineInputBorder(borderRadius: StandbyRadius.buttonRadius),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _nicknameController,
            style: TextStyle(color: context.textColor),
            decoration: InputDecoration(
              hintText: '输入昵称',
              hintStyle: TextStyle(color: context.text3Color),
              border: OutlineInputBorder(borderRadius: StandbyRadius.buttonRadius),
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _save,
            style: ElevatedButton.styleFrom(
              backgroundColor: StandbyColors.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: StandbyRadius.buttonRadius),
            ),
            child: const Text('保存'),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}
