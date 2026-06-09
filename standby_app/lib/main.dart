import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app/app.dart';
import 'shared/services/api_service.dart';
import 'shared/services/storage_service.dart';
import 'core/constants/app_constants.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 设置 API 基础地址
  ApiService.setBaseUrl(AppConstants.apiBaseUrl);

  // 初始化本地存储
  final storage = StorageService();
  await storage.init();

  // 检查是否已注册，如果已注册则初始化 API
  final isRegistered = storage.isRegistered;
  if (isRegistered) {
    String? fp = storage.deviceFingerprint;
    if (fp == null) {
      fp = sha256.convert(utf8.encode('standby_device_${DateTime.now().millisecondsSinceEpoch}')).toString();
      await storage.setDeviceFingerprint(fp);
    }
    ApiService().init(fp).catchError((e) {
      print('API initialization failed: $e');
    });
  }

  runApp(const ProviderScope(child: StandbyApp()));
}
