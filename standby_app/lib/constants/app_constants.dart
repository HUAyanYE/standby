/// 应用常量
class AppConstants {
  // 版本信息
  static const String appName = 'Standby';
  static const String appVersion = '0.3.0';
  static const int buildNumber = 13;
  static const String fullVersion = '$appVersion+$buildNumber';
  
  // API 配置
  static const String apiBaseUrl = 'http://10.0.2.2:8080';
  static const String apiVersion = 'v1';
  
  // 设备类型
  static const String deviceType = 'PHONE';
  static const String osVersion = 'Android 14';
  
  // 其他常量
  static const int apiTimeoutSeconds = 10;
  static const int maxAnchorsPerPage = 20;
  static const int minContentLength = 100;
}