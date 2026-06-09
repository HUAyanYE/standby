import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../shared/providers/feature_unlock_provider.dart';

/// Shell 页面 — 包含底部导航栏的 4 个 Tab
/// 遇见 | 记录 | 痕迹 | 我
class ShellScreen extends ConsumerWidget {
  final Widget child;

  const ShellScreen({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).uri.toString();
    final traceUnlocked = ref.watch(traceUnlockProvider);

    // 计算当前选中的 tab index
    int currentIndex = 0;
    if (location.startsWith('/record')) {
      currentIndex = 1;
    } else if (location.startsWith('/trace')) {
      currentIndex = 2;
    } else if (location.startsWith('/me')) {
      currentIndex = 3;
    }

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          switch (index) {
            case 0:
              context.go('/meet');
              break;
            case 1:
              context.go('/record');
              break;
            case 2:
              if (traceUnlocked) {
                context.go('/trace');
              } else {
                _showLockedSnackBar(context);
              }
              break;
            case 3:
              context.go('/me');
              break;
          }
        },
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.favorite_outline),
            selectedIcon: Icon(Icons.favorite),
            label: '遇见',
          ),
          const NavigationDestination(
            icon: Icon(Icons.edit_note_outlined),
            selectedIcon: Icon(Icons.edit_note),
            label: '记录',
          ),
          NavigationDestination(
            icon: traceUnlocked
                ? const Icon(Icons.auto_awesome_outlined)
                : const Icon(Icons.lock_outline),
            selectedIcon: traceUnlocked
                ? const Icon(Icons.auto_awesome)
                : const Icon(Icons.lock),
            label: '痕迹',
          ),
          const NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: '我',
          ),
        ],
      ),
    );
  }

  void _showLockedSnackBar(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('痕迹需要至少 10 次共鸣后解锁'),
        duration: Duration(seconds: 2),
      ),
    );
  }
}
