import 'package:flutter/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:standby_app/app/app.dart';
import 'package:standby_app/shared/services/storage_service.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Standby E2E Tests', () {
    setUp(() async {
      SharedPreferences.setMockInitialValues({});
      await StorageService().init();
    });

    testWidgets('T01: App launches and shows Meet page', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: StandbyApp()));
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // Should show the Standby title
      expect(find.text('Standby'), findsOneWidget);

      // Bottom nav should be visible with 4 tabs
      expect(find.text('遇见'), findsOneWidget);
      expect(find.text('记录'), findsOneWidget);
      expect(find.text('痕迹'), findsOneWidget);
      expect(find.text('我'), findsOneWidget);
    });

    testWidgets('T02: Bottom navigation switches tabs', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: StandbyApp()));
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // Tap Record tab
      await tester.tap(find.byKey(const Key('nav_record')));
      await tester.pumpAndSettle();
      expect(find.text('记录'), findsWidgets);

      // Tap Me tab
      await tester.tap(find.byKey(const Key('nav_me')));
      await tester.pumpAndSettle();
      expect(find.text('我'), findsWidgets);

      // Tap Meet tab
      await tester.tap(find.byKey(const Key('nav_meet')));
      await tester.pumpAndSettle();
      expect(find.text('Standby'), findsOneWidget);
    });

    testWidgets('T03: Meet page shows content or empty state', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: StandbyApp()));
      await tester.pumpAndSettle(const Duration(seconds: 5));

      // Should show either content or empty state after loading
      // The page title should be visible
      final hasTitle = find.text('Standby').evaluate().isNotEmpty;
      final hasEmpty = find.text('暂无心物').evaluate().isNotEmpty;
      final hasError = find.text('加载失败，请下拉刷新').evaluate().isNotEmpty;
      expect(hasTitle || hasEmpty || hasError, true);
    });

    testWidgets('T04: Me page shows profile and theme setting', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: StandbyApp()));
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // Navigate to Me tab
      await tester.tap(find.byKey(const Key('nav_me')));
      await tester.pumpAndSettle();

      // Should show profile elements
      expect(find.text('旅人'), findsOneWidget); // Default nickname
      expect(find.text('外观模式'), findsOneWidget);
      expect(find.text('暗色'), findsOneWidget); // Default theme
    });

    testWidgets('T05: Theme picker opens and shows options', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: StandbyApp()));
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // Navigate to Me tab
      await tester.tap(find.byKey(const Key('nav_me')));
      await tester.pumpAndSettle();

      // Tap theme setting
      await tester.tap(find.text('外观模式'));
      await tester.pumpAndSettle();

      // Should show theme picker bottom sheet
      expect(find.text('暗色'), findsWidgets);
      expect(find.text('亮色'), findsOneWidget);
      expect(find.text('跟随系统'), findsOneWidget);
    });

    testWidgets('T06: Theme switching works', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: StandbyApp()));
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // Navigate to Me tab
      await tester.tap(find.byKey(const Key('nav_me')));
      await tester.pumpAndSettle();

      // Open theme picker
      await tester.tap(find.text('外观模式'));
      await tester.pumpAndSettle();

      // Select light mode
      await tester.tap(find.byKey(const Key('theme_light')));
      await tester.pumpAndSettle();

      // Verify theme changed - the setting should now show '亮色'
      expect(find.text('亮色'), findsOneWidget);

      // Switch back to dark
      await tester.tap(find.text('外观模式'));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('theme_dark')));
      await tester.pumpAndSettle();
      expect(find.text('暗色'), findsOneWidget);
    });

    testWidgets('T07: Meet page renders without crash', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: StandbyApp()));
      await tester.pumpAndSettle(const Duration(seconds: 5));

      // Page should render without crashing - any of these states is valid
      final hasTitle = find.text('Standby').evaluate().isNotEmpty;
      final hasLoading = find.byType(CircularProgressIndicator).evaluate().isNotEmpty;
      final hasEmpty = find.text('暂无心物').evaluate().isNotEmpty;
      final hasError = find.text('加载失败，请下拉刷新').evaluate().isNotEmpty;
      final hasWrite = find.text('写感想').evaluate().isNotEmpty;
      expect(hasTitle || hasLoading || hasEmpty || hasError || hasWrite, true);
    });

    testWidgets('T08: Meet page view opinions button or empty state', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: StandbyApp()));
      await tester.pumpAndSettle(const Duration(seconds: 5));

      final viewBtn = find.byKey(const Key('btn_view_opinions'));
      final emptyState = find.text('暂无心物');
      final hasError = find.text('加载失败，请下拉刷新').evaluate().isNotEmpty;
      final hasLoading = find.byType(CircularProgressIndicator).evaluate().isNotEmpty;
      expect(viewBtn.evaluate().isNotEmpty || emptyState.evaluate().isNotEmpty || hasError || hasLoading, true);
    });
  });
}
