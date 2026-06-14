import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ShellScreen extends ConsumerWidget {
  final Widget child;

  const ShellScreen({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).uri.toString();

    int currentIndex = 0;
    if (location.startsWith('/record')) {
      currentIndex = 1;
    } else if (location.startsWith('/trace')) {
      currentIndex = 2;
    } else if (location == '/me' || location.startsWith('/me?')) {
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
              context.go('/trace');
              break;
            case 3:
              context.go('/me');
              break;
          }
        },
        destinations: const [
          NavigationDestination(
            key: Key('nav_meet'),
            icon: Icon(Icons.favorite_outline),
            selectedIcon: Icon(Icons.favorite),
            label: '遇见',
          ),
          NavigationDestination(
            key: Key('nav_record'),
            icon: Icon(Icons.edit_note_outlined),
            selectedIcon: Icon(Icons.edit_note),
            label: '记录',
          ),
          NavigationDestination(
            key: Key('nav_trace'),
            icon: Icon(Icons.auto_awesome_outlined),
            selectedIcon: Icon(Icons.auto_awesome),
            label: '痕迹',
          ),
          NavigationDestination(
            key: Key('nav_me'),
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: '我',
          ),
        ],
      ),
    );
  }
}
