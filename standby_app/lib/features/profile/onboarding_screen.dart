import 'package:flutter/material.dart';
import '../../app/theme.dart';
import '../../app/theme_colors.dart';

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
    _OnboardingPage(
      title: '',
      content: '在 AI 让一切都可以\n被伪造的时代，\n\n重建人与人之间的真实连接。',
      subtitle: '有共鸣才有真实感想',
      showButton: false,
    ),
    _OnboardingPage(
      title: '',
      content: '这里没有点赞，\n只有真实的感受。\n\n不追求被看见，\n而是被理解。\n\n每一次共鸣，\n都是一次相遇。',
      subtitle: '',
      showButton: false,
    ),
    _OnboardingPage(
      title: '',
      content: '强实名注册，\n全匿名展示。\n\n你的身份是信任的奖励，\n不是社交的入场券。\n\n在这里，\n你可以安全地做自己。',
      subtitle: '',
      showButton: false,
    ),
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
      backgroundColor: context.bgColor,
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _pages.length,
                onPageChanged: (index) {
                  setState(() => _currentPage = index);
                },
                itemBuilder: (context, index) {
                  return _AnimatedOnboardingPage(
                    page: _pages[index],
                    isActive: _currentPage == index,
                  );
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 24),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(
                  _pages.length,
                  (index) => AnimatedContainer(
                    duration: StandbyDuration.normal,
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    width: _currentPage == index ? 24 : 8,
                    height: 8,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(4),
                      color: _currentPage == index
                          ? StandbyColors.primary
                          : context.text3Color,
                    ),
                  ),
                ),
              ),
            ),
            if (_pages[_currentPage].showButton)
              Padding(
                padding: const EdgeInsets.fromLTRB(32, 0, 32, 32),
                child: SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    onPressed: widget.onDone,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: StandbyColors.primary,
                      foregroundColor: context.bgColor,
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
                  style: TextStyle(color: context.text3Color),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _AnimatedOnboardingPage extends StatefulWidget {
  final _OnboardingPage page;
  final bool isActive;

  const _AnimatedOnboardingPage({required this.page, required this.isActive});

  @override
  State<_AnimatedOnboardingPage> createState() => _AnimatedOnboardingPageState();
}

class _AnimatedOnboardingPageState extends State<_AnimatedOnboardingPage>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _opacity;
  late Animation<Offset> _offset;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: StandbyDuration.slow,
    );
    _opacity = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
    );
    _offset = Tween<Offset>(begin: const Offset(0, 0.1), end: Offset.zero).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
    );
    if (widget.isActive) _controller.forward();
  }

  @override
  void didUpdateWidget(_AnimatedOnboardingPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isActive && !oldWidget.isActive) {
      _controller.reset();
      _controller.forward();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _opacity,
      child: SlideTransition(
        position: _offset,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (widget.page.title.isNotEmpty) ...[
                Text(
                  widget.page.title,
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
              ],
              Text(
                widget.page.content,
                style: TextStyle(fontSize: 18, height: 1.8, color: context.textColor),
                textAlign: TextAlign.center,
              ),
              if (widget.page.subtitle.isNotEmpty) ...[
                const SizedBox(height: 32),
                Text(
                  widget.page.subtitle,
                  style: TextStyle(fontSize: 14, color: context.text2Color),
                  textAlign: TextAlign.center,
                ),
              ],
            ],
          ),
        ),
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
