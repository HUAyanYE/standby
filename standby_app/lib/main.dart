import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'services/media_service.dart';
import 'services/storage_service.dart';
import 'models/user_identity.dart';
import 'screens/onboarding_screen.dart';
import 'screens/register_screen.dart';
import 'screens/main_screen.dart';
import 'constants/app_constants.dart';

// 全局导航 Key
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 设置 API 基础地址 (Android 模拟器使用 10.0.2.2)
  ApiService.setBaseUrl(AppConstants.apiBaseUrl);

  // 初始化本地存储
  final storage = StorageService();
  await storage.init();

  runApp(StandbyApp(storage: storage));
}

class StandbyApp extends StatelessWidget {
  final StorageService storage;

  const StandbyApp({super.key, required this.storage});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      navigatorKey: navigatorKey,
      title: 'Standby',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: Colors.indigo,
        useMaterial3: true,
        brightness: Brightness.light,
      ),
      home: SplashScreen(storage: storage),
    );
  }
}

/// 启动页 — 根据状态决定进入哪个页面
class SplashScreen extends StatefulWidget {
  final StorageService storage;

  const SplashScreen({super.key, required this.storage});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  final _api = ApiService();
  late final _mediaService = MediaService(_api);

  @override
  void initState() {
    super.initState();
    // 等待第一帧渲染完成后再导航
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _init();
    });
  }

  Future<void> _init() async {
    try {
      // 检查是否已完成 Onboarding
      final isOnboardingDone = widget.storage.isOnboardingDone;

      // 检查是否已注册
      final isRegistered = widget.storage.isRegistered;

      print('Onboarding done: $isOnboardingDone, Registered: $isRegistered');

      if (!isOnboardingDone) {
        // 进入 Onboarding
        _navigateToOnboarding();
      } else if (!isRegistered) {
        // 进入注册页
        _navigateToRegister();
      } else {
        // 已注册，进入主界面
        await _initApiAndNavigate();
      }
    } catch (e) {
      print('Init error: $e');
      // 出错时也进入 Onboarding
      _navigateToOnboarding();
    }
  }

  void _navigateToOnboarding() {
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (ctx) => OnboardingScreen(
          onDone: () {
            print('>>> Onboarding onDone called');
            widget.storage.setOnboardingDone();
            // 使用新的 context 导航
            Navigator.of(ctx).pushReplacement(
              MaterialPageRoute(
                builder: (_) => RegisterScreen(
                  onRegister: _handleRegister,
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  void _navigateToRegister() {
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => RegisterScreen(
          onRegister: _handleRegister,
        ),
      ),
    );
  }

  Future<void> _handleRegister(String nickname, String avatar) async {
    print('>>> _handleRegister called: nickname=$nickname, avatar=$avatar');

    // 保存身份信息
    final identity = UserIdentity(nickname: nickname, avatar: avatar);
    await widget.storage.setUserIdentity(identity.toJson());
    print('>>> Identity saved');

    // 生成或加载设备指纹
    String? fp = widget.storage.deviceFingerprint;
    if (fp == null) {
      fp = sha256.convert(utf8.encode('standby_device_${DateTime.now().millisecondsSinceEpoch}')).toString();
      await widget.storage.setDeviceFingerprint(fp);
      print('>>> Device fingerprint created: $fp');
    } else {
      print('>>> Device fingerprint loaded: $fp');
    }

    // 获取用户身份
    final userIdentity = identity;
    print('>>> User identity: ${userIdentity.nickname} ${userIdentity.avatar}');

    // 使用全局 NavigatorKey 导航
    print('>>> Navigating to MainScreen...');
    navigatorKey.currentState?.pushReplacement(
      MaterialPageRoute(
        builder: (_) => MainScreen(api: _api, mediaService: _mediaService, userIdentity: userIdentity),
      ),
    );
    print('>>> Navigation complete');

    // 后台异步初始化 API（不阻塞 UI）
    print('>>> Initializing API in background...');
    _api.init(fp).then((_) {
      print('>>> API initialized successfully');
    }).catchError((e) {
      print('>>> API initialization failed: $e');
    });
  }

  Future<void> _initApiAndNavigate() async {
    if (!mounted) return;
    // 生成或加载设备指纹
    String? fp = widget.storage.deviceFingerprint;
    if (fp == null) {
      fp = sha256.convert(utf8.encode('standby_device_${DateTime.now().millisecondsSinceEpoch}')).toString();
      await widget.storage.setDeviceFingerprint(fp);
    }

    // 获取用户身份
    final identityData = widget.storage.userIdentity;
    final userIdentity = identityData != null
        ? UserIdentity.fromJson(identityData)
        : UserIdentity(nickname: '旅人', avatar: '🌙');

    // 进入主界面
    if (mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => MainScreen(api: _api, mediaService: _mediaService, userIdentity: userIdentity),
        ),
      );
    }

    // 后台异步初始化 API
    _api.init(fp).catchError((e) {
      print('API initialization failed: $e');
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Standby',
              style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                fontWeight: FontWeight.bold,
                color: Colors.indigo,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '有共鸣才有真实感想',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 32),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}
