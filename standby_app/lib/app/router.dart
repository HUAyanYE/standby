import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../features/seedstone/meet_screen.dart';
import '../features/record/record_screen.dart';
import '../features/perception/trace_screen.dart';
import '../features/profile/me_screen.dart';
import '../features/confidant/confidant_page.dart';
import '../features/seedstone/seedstone_detail_page.dart';
import '../features/seedstone/publish_screen.dart';
import 'shell_screen.dart';

/// GoRouter 配置 — 命名路由
final goRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/meet',
    routes: [
      // 底部导航 Shell Route
      ShellRoute(
        builder: (context, state, child) => ShellScreen(child: child),
        routes: [
          GoRoute(
            path: '/meet',
            name: 'meet',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: MeetScreen(),
            ),
          ),
          GoRoute(
            path: '/record',
            name: 'record',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: RecordScreen(),
            ),
          ),
          GoRoute(
            path: '/trace',
            name: 'trace',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: TraceScreen(),
            ),
          ),
          GoRoute(
            path: '/me',
            name: 'me',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: MeScreen(),
            ),
          ),
        ],
      ),
      // 独立页面（无底部导航）
      GoRoute(
        path: '/confidant',
        name: 'confidant',
        builder: (context, state) => const ConfidantPage(),
      ),
      GoRoute(
        path: '/seedstone/:id',
        name: 'seedstoneDetail',
        builder: (context, state) => SeedstoneDetailPage(
          seedstoneId: state.pathParameters['id']!,
        ),
      ),
      GoRoute(
        path: '/publish',
        name: 'publish',
        builder: (context, state) => const PublishScreen(),
      ),
    ],
  );
});
