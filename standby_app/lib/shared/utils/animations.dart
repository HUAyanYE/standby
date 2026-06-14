import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../app/theme.dart';

class StandbyAnimations {
  StandbyAnimations._();

  static CustomTransitionPage<T> fadeSlidePage<T>(Widget page) {
    return CustomTransitionPage<T>(
      transitionDuration: StandbyDuration.normal,
      reverseTransitionDuration: StandbyDuration.fast,
      child: page,
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        final curved = CurvedAnimation(
          parent: animation,
          curve: Curves.easeOutCubic,
        );
        return FadeTransition(
          opacity: curved,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0.05, 0),
              end: Offset.zero,
            ).animate(curved),
            child: child,
          ),
        );
      },
    );
  }

  static Widget fadeIn({
    required Widget child,
    Duration duration = StandbyDuration.normal,
    Duration delay = Duration.zero,
    Offset offset = Offset.zero,
  }) {
    return _FadeInWidget(
      duration: duration,
      delay: delay,
      offset: offset,
      child: child,
    );
  }

  static Widget staggeredList({
    required List<Widget> children,
    Duration stagger = const Duration(milliseconds: 60),
  }) {
    return Column(
      children: List.generate(children.length, (i) {
        return fadeIn(
          child: children[i],
          delay: stagger * i,
          offset: const Offset(0, 0.05),
        );
      }),
    );
  }
}

class _FadeInWidget extends StatefulWidget {
  final Widget child;
  final Duration duration;
  final Duration delay;
  final Offset offset;

  const _FadeInWidget({
    required this.child,
    required this.duration,
    required this.delay,
    required this.offset,
  });

  @override
  State<_FadeInWidget> createState() => _FadeInWidgetState();
}

class _FadeInWidgetState extends State<_FadeInWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _opacity;
  late Animation<Offset> _position;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: widget.duration,
    );
    _opacity = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
    );
    _position = Tween<Offset>(begin: widget.offset, end: Offset.zero).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
    );

    if (widget.delay == Duration.zero) {
      _controller.forward();
    } else {
      Future.delayed(widget.delay, () {
        if (mounted) _controller.forward();
      });
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
        position: _position,
        child: widget.child,
      ),
    );
  }
}
