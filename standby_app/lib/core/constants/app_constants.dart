import 'package:flutter/foundation.dart';

class AppConstants {
  static const String appName = 'Standby';
  static const String appVersion = '0.3.0';
  static const int buildNumber = 13;
  static const String fullVersion = '$appVersion+$buildNumber';

  static String get apiBaseUrl {
    const envUrl = String.fromEnvironment('API_BASE_URL');
    if (envUrl.isNotEmpty) return envUrl;
    if (kIsWeb) return 'http://localhost:8080';
    return 'http://10.0.2.2:8080';
  }

  static const String apiVersion = 'v1';
  static const String deviceType = 'PHONE';
  static const String osVersion = 'Android 14';
  static const int apiTimeoutSeconds = 10;
  static const int maxAnchorsPerPage = 20;
  static const int minContentLength = 100;
}