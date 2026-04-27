import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/media_service.dart';
import '../models/user_identity.dart';
import 'meet_screen.dart';
import 'record_screen.dart';
import 'trace_screen.dart';
import 'me_screen.dart';

/// 主界面 — 底部 Tab 导航
class MainScreen extends StatefulWidget {
  final ApiService api;
  final MediaService mediaService;
  final UserIdentity userIdentity;

  const MainScreen({
    super.key,
    required this.api,
    required this.mediaService,
    required this.userIdentity,
  });

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;
  String? _targetAnchorId;
  final GlobalKey<RecordScreenState> _recordScreenKey = GlobalKey<RecordScreenState>();

  /// 导航到遇见页的指定锚点
  void _navigateToAnchor(String anchorId) {
    setState(() {
      _targetAnchorId = anchorId;
      _currentIndex = 0; // 切换到遇见页
    });
  }

  /// 通知记录页刷新数据
  void _onReactionAdded() {
    _recordScreenKey.currentState?.loadData();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: [
          // 遇见页 - 根据 targetAnchorId 重新构建
          MeetScreen(
            key: _targetAnchorId != null
                ? ValueKey('meet_$_targetAnchorId')
                : const ValueKey('meet_default'),
            api: widget.api,
            initialAnchorId: _targetAnchorId,
            onReactionAdded: _onReactionAdded,
          ),
          RecordScreen(
            key: _recordScreenKey,
            api: widget.api,
            mediaService: widget.mediaService,
            onNavigateToAnchor: _navigateToAnchor,
          ),
          TraceScreen(api: widget.api),
          MeScreen(userIdentity: widget.userIdentity),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() => _currentIndex = index);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.favorite_outline),
            selectedIcon: Icon(Icons.favorite, color: Colors.indigo),
            label: '遇见',
          ),
          NavigationDestination(
            icon: Icon(Icons.edit_note_outlined),
            selectedIcon: Icon(Icons.edit_note, color: Colors.indigo),
            label: '记录',
          ),
          NavigationDestination(
            icon: Icon(Icons.auto_awesome_outlined),
            selectedIcon: Icon(Icons.auto_awesome, color: Colors.indigo),
            label: '痕迹',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person, color: Colors.indigo),
            label: '我',
          ),
        ],
      ),
    );
  }
}
