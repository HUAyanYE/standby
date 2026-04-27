import 'package:flutter/material.dart';

/// Onboarding 页面 — 产品理念展示
class OnboardingScreen extends StatefulWidget {
  final VoidCallback? onDone;

  const OnboardingScreen({super.key, this.onDone});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _controller = PageController();
  int _currentPage = 0;

  final List<_OnboardingPage> _pages = [
    // 第 1 页：产品定位
    _OnboardingPage(
      title: '',
      content: '在 AI 让一切都可以\n被伪造的时代，\n\n重建人与人之间的真实连接。',
      subtitle: '有共鸣才有真实感想',
      showButton: false,
    ),
    // 第 2 页：核心理念
    _OnboardingPage(
      title: '',
      content: '这里没有点赞，\n只有真实的感受。\n\n不追求被看见，\n而是被理解。\n\n每一次共鸣，\n都是一次相遇。',
      subtitle: '',
      showButton: false,
    ),
    // 第 3 页：匿名机制
    _OnboardingPage(
      title: '',
      content: '强实名注册，\n全匿名展示。\n\n你的身份是信任的奖励，\n不是社交的入场券。\n\n在这里，\n你可以安全地做自己。',
      subtitle: '',
      showButton: false,
    ),
    // 第 4 页：使用方式
    _OnboardingPage(
      title: '如何使用 Standby？',
      content: '❤️ 遇见\n浏览锚点，表达你的共鸣\n\n📝 记录\n回顾你的表达轨迹\n\n🔍 痕迹\n发现与你共鸣的人',
      subtitle: '',
      showButton: true,
    ),
  ];

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            // 页面内容
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _pages.length,
                onPageChanged: (index) {
                  setState(() => _currentPage = index);
                },
                itemBuilder: (context, index) {
                  return _buildPage(_pages[index]);
                },
              ),
            ),

            // 指示器
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 24),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(
                  _pages.length,
                  (index) => Container(
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _currentPage == index
                          ? Colors.indigo
                          : Colors.grey.shade300,
                    ),
                  ),
                ),
              ),
            ),

            // 底部按钮
            if (_pages[_currentPage].showButton)
              Padding(
                padding: const EdgeInsets.fromLTRB(32, 0, 32, 32),
                child: SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    onPressed: widget.onDone,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.indigo,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                    child: const Text(
                      '开始使用 Standby',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              )
            else
              Padding(
                padding: const EdgeInsets.fromLTRB(32, 0, 32, 32),
                child: Text(
                  '滑动继续 →',
                  style: TextStyle(color: Colors.grey.shade500),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildPage(_OnboardingPage page) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (page.title.isNotEmpty) ...[
            Text(
              page.title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
          ],
          Text(
            page.content,
            style: const TextStyle(
              fontSize: 18,
              height: 1.8,
              color: Colors.black87,
            ),
            textAlign: TextAlign.center,
          ),
          if (page.subtitle.isNotEmpty) ...[
            const SizedBox(height: 32),
            Text(
              page.subtitle,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade600,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ],
      ),
    );
  }
}

class _OnboardingPage {
  final String title;
  final String content;
  final String subtitle;
  final bool showButton;

  _OnboardingPage({
    required this.title,
    required this.content,
    required this.subtitle,
    required this.showButton,
  });
}
