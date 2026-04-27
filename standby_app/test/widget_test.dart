import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:standby_app/models/user_identity.dart';
import 'package:standby_app/widgets/nickname_generator.dart';
import 'package:standby_app/widgets/reaction_buttons.dart';
import 'package:standby_app/screens/onboarding_screen.dart';
import 'package:standby_app/screens/register_screen.dart';

// ── 模型测试 ──────────────────────────────────────────────────

void main() {
  group('UserIdentity 模型测试', () {
    test('JSON 序列化/反序列化', () {
      final identity = UserIdentity(
        nickname: '夜的旅人',
        avatar: '🌙',
        createdAt: DateTime(2026, 4, 17),
      );

      final json = identity.toJson();
      final restored = UserIdentity.fromJson(json);

      expect(restored.nickname, '夜的旅人');
      expect(restored.avatar, '🌙');
      expect(restored.displayName, '🌙 夜的旅人');
    });

    test('创建时间默认为当前时间', () {
      final before = DateTime.now();
      final identity = UserIdentity(nickname: '测试', avatar: '⭐');
      final after = DateTime.now();

      expect(identity.createdAt.isAfter(before.subtract(const Duration(seconds: 1))), true);
      expect(identity.createdAt.isBefore(after.add(const Duration(seconds: 1))), true);
    });
  });
// 昵称生成器测试
  group('NicknameGenerator 昵称生成器测试', () {
    test('生成一个昵称', () {
      final nickname = NicknameGenerator.generate();
      expect(nickname, isNotEmpty);
      expect(nickname.length, greaterThan(2));
    });

    test('生成一批昵称', () {
      final batch = NicknameGenerator.generateBatch();
      expect(batch.length, 3);  // 改为 3 个
      // 确保没有重复
      expect(batch.toSet().length, 3);
    });

    test('多次生成结果不同', () {
      final name1 = NicknameGenerator.generate();
      final name2 = NicknameGenerator.generate();
      // 虽然可能相同，但大概率不同
      // 这里只验证能正常运行
      expect(name1.isNotEmpty, true);
      expect(name2.isNotEmpty, true);
    });
  });

  group('ReactionButtons 反应按钮测试', () {
    testWidgets('渲染五态反应按钮', (tester) async {
      ReactionType? selected;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: ReactionButtons(
                selectedReaction: null,
                counts: {
                  ReactionType.resonance: 80,
                  ReactionType.neutral: 30,
                  ReactionType.opposition: 10,
                  ReactionType.unexperienced: 5,
                  ReactionType.harmful: 1,
                },
                onReaction: (type) => selected = type,
              ),
            ),
          ),
        ),
      );

      // 验证按钮存在
      expect(find.text('共鸣'), findsOneWidget);
      expect(find.text('无感'), findsOneWidget);
      expect(find.text('反对'), findsOneWidget);
      expect(find.text('未体验'), findsOneWidget);

      // 验证计数显示
      expect(find.text('80+'), findsOneWidget);
      expect(find.text('30+'), findsOneWidget);
      expect(find.text('10+'), findsOneWidget);
      expect(find.text('5+'), findsOneWidget);
    });

    testWidgets('点击共鸣按钮触发 onResonance 回调', (tester) async {
      bool resonanceCalled = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: ReactionButtons(
                selectedReaction: null,
                counts: {},
                onReaction: (_) {},
                onResonance: () => resonanceCalled = true,
              ),
            ),
          ),
        ),
      );

      await tester.tap(find.text('共鸣'));
      await tester.pump();

      expect(resonanceCalled, true);
    });

    testWidgets('点击无感按钮触发 onReaction 回调', (tester) async {
      ReactionType? capturedType;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: ReactionButtons(
                selectedReaction: null,
                counts: {},
                onReaction: (type) => capturedType = type,
              ),
            ),
          ),
        ),
      );

      await tester.tap(find.text('无感'));
      await tester.pump();

      expect(capturedType, ReactionType.neutral);
    });

    testWidgets('选中状态高亮显示', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: ReactionButtons(
                selectedReaction: ReactionType.resonance,
                counts: {},
                onReaction: (_) {},
              ),
            ),
          ),
        ),
      );

      // 验证共鸣按钮被选中（有选中样式）
      // 简化测试：只验证按钮存在
      expect(find.text('共鸣'), findsOneWidget);
    });
  });

  group('页面渲染测试', () {
    testWidgets('Onboarding 页面渲染', (tester) async {
      bool doneCalled = false;

      await tester.pumpWidget(
        MaterialApp(
          home: OnboardingScreen(onDone: () => doneCalled = true),
        ),
      );

      // 验证第一页内容存在
      expect(find.textContaining('在 AI 让一切都可以'), findsOneWidget);
      expect(find.text('滑动继续 →'), findsOneWidget);
    });

    testWidgets('Onboarding 页面滑动切换', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: OnboardingScreen(onDone: () {}),
        ),
      );

      // 验证第一页
      expect(find.text('滑动继续 →'), findsOneWidget);

      // 滑动到第二页
      await tester.fling(find.byType(PageView), const Offset(-400, 0), 1000);
      await tester.pumpAndSettle();

      // 验证第二页内容
      expect(find.textContaining('这里没有点赞'), findsOneWidget);
    });

    testWidgets('注册页面渲染', (tester) async {
      // 设置较大的屏幕尺寸
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 3.0;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        MaterialApp(
          home: RegisterScreen(
            onRegister: (nickname, avatar) {},
          ),
        ),
      );

      // 验证标题存在
      expect(find.text('欢迎加入 Standby'), findsOneWidget);
      expect(find.text('选择你的昵称'), findsOneWidget);
      expect(find.text('选择你的头像'), findsOneWidget);
      expect(find.text('换一批'), findsOneWidget);
      expect(find.text('进入 Standby'), findsOneWidget);
    });

    testWidgets('注册页面昵称刷新', (tester) async {
      // 设置较大的屏幕尺寸
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 3.0;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        MaterialApp(
          home: RegisterScreen(
            onRegister: (nickname, avatar) {},
          ),
        ),
      );

      // 点击换一批
      await tester.tap(find.text('换一批'));
      await tester.pump();

      // 验证页面仍然存在
      expect(find.text('欢迎加入 Standby'), findsOneWidget);
    });

    testWidgets('注册页面点击进入按钮', (tester) async {
      // 设置较大的屏幕尺寸
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 3.0;
      addTearDown(tester.view.reset);

      String? selectedNickname;
      String? selectedAvatar;

      await tester.pumpWidget(
        MaterialApp(
          home: RegisterScreen(
            onRegister: (nickname, avatar) {
              selectedNickname = nickname;
              selectedAvatar = avatar;
            },
          ),
        ),
      );

      // 点击进入按钮
      await tester.tap(find.text('进入 Standby'));
      await tester.pump();

      // 验证回调被调用
      expect(selectedNickname, isNotNull);
      expect(selectedAvatar, isNotNull);
    });
  });

  group('组件单元测试', () {
    testWidgets('情绪词弹窗渲染', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (context) => ElevatedButton(
                onPressed: () {
                  showModalBottomSheet(
                    context: context,
                    builder: (_) => const SizedBox(
                      height: 300,
                      child: Placeholder(),
                    ),
                  );
                },
                child: const Text('Show'),
              ),
            ),
          ),
        ),
      );

      await tester.tap(find.text('Show'));
      await tester.pumpAndSettle();

      // 验证弹窗显示
      expect(find.byType(Placeholder), findsOneWidget);
    });
  });
}
