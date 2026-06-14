import 'package:flutter/material.dart';
import 'theme.dart';

/// 主题感知的颜色访问器
/// 根据当前主题亮度返回正确的颜色
extension StandbyThemeColors on BuildContext {
  bool get isDark => Theme.of(this).brightness == Brightness.dark;

  Color get bgColor => isDark ? StandbyColors.background : StandbyColors.lightBackground;
  Color get surface1 => isDark ? StandbyColors.surface1 : StandbyColors.lightSurface1;
  Color get surface2 => isDark ? StandbyColors.surface2 : StandbyColors.lightSurface2;
  Color get surface3 => isDark ? StandbyColors.surface3 : StandbyColors.lightSurface3;
  Color get textColor => isDark ? StandbyColors.text : StandbyColors.lightText;
  Color get text2Color => isDark ? StandbyColors.text2 : StandbyColors.lightText2;
  Color get text3Color => isDark ? StandbyColors.text3 : StandbyColors.lightText3;
  Color get borderColor => isDark ? StandbyColors.border : StandbyColors.lightBorder;
}
