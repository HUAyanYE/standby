import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app/app.dart';
import 'shared/services/api_service.dart';
import 'shared/services/storage_service.dart';
import 'core/constants/app_constants.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  FlutterError.onError = (details) {
    FlutterError.presentError(details);
    if (kReleaseMode) {
      // TODO: send to crash reporting service
    }
  };

  ApiService.setBaseUrl(AppConstants.apiBaseUrl);

  final storage = StorageService();
  await storage.init();

  if (storage.isRegistered) {
    String? fp = storage.deviceFingerprint;
    if (fp == null) {
      fp = sha256.convert(utf8.encode('standby_device_${DateTime.now().millisecondsSinceEpoch}')).toString();
      await storage.setDeviceFingerprint(fp);
    }
    ApiService().init(fp).catchError((e) {
      debugPrint('API initialization failed: $e');
    });
  }

  runApp(const ProviderScope(child: StandbyApp()));
}
