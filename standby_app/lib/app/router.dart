import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../features/seedstone/meet_screen.dart';
import '../features/record/record_screen.dart';
import '../features/perception/trace_screen.dart';
import '../features/profile/me_screen.dart';
import '../features/confidant/confidant_page.dart';
import '../features/seedstone/seedstone_detail_page.dart';
import '../features/seedstone/publish_screen.dart';
import '../features/profile/onboarding_screen.dart';
import '../features/profile/register_screen.dart';
import '../shared/services/storage_service.dart';
import '../shared/utils/animations.dart';
import 'shell_screen.dart';

final goRouterProvider = Provider<GoRouter>((ref) {
  final storage = StorageService();

  String initialLocation() {
    if (!storage.isOnboardingDone) return '/onboarding';
    if (!storage.isRegistered) return '/register';
    return '/meet';
  }

  return GoRouter(
    initialLocation: initialLocation(),
    routes: [
      GoRoute(
        path: '/onboarding',
        name: 'onboarding',
        builder: (context, state) => OnboardingScreen(
          onDone: () {
            storage.setOnboardingDone();
            if (storage.isRegistered) {
              context.go('/meet');
            } else {
              context.go('/register');
            }
          },
        ),
      ),
      GoRoute(
        path: '/register',
        name: 'register',
        builder: (context, state) => RegisterScreen(
          onRegister: (nickname, avatar) async {
            await storage.setUserIdentity({
              'device_id': storage.deviceFingerprint ?? '',
              'set_nickname': nickname,
              'set_avatar': avatar,
              'created_at': DateTime.now().millisecondsSinceEpoch,
            });
            context.go('/meet');
          },
        ),
      ),
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
      GoRoute(
        path: '/confidant',
        name: 'confidant',
        pageBuilder: (context, state) => StandbyAnimations.fadeSlidePage(
          const ConfidantPage(),
        ),
      ),
      GoRoute(
        path: '/seedstone/:id',
        name: 'seedstoneDetail',
        pageBuilder: (context, state) => StandbyAnimations.fadeSlidePage(
          SeedstoneDetailPage(seedstoneId: state.pathParameters['id']!),
        ),
      ),
      GoRoute(
        path: '/publish',
        name: 'publish',
        pageBuilder: (context, state) => StandbyAnimations.fadeSlidePage(
          const PublishScreen(),
        ),
      ),
    ],
  );
});
