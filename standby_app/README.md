# Standby Flutter App

> v0.2.9+12 | 包名: `com.standby.standby_app`

## 快速启动

### 构建

```bash
# 从 WSL 调用 Windows Flutter SDK
cd /mnt/d/Hermes/standby/standby_app
cmd.exe /c "flutter pub get"
cmd.exe /c "flutter build apk --release"
```

### 安装到模拟器

```bash
cmd.exe /c "flutter install --device-id emulator-5554"
```

### 安装到真机

```bash
cmd.exe /c "flutter install --device-id <设备ID>"
```

## 配置

### API 地址

`lib/constants/app_constants.dart` 中的 `apiBaseUrl`:

```dart
// Android 模拟器 (本机)
static const String apiBaseUrl = 'http://10.0.2.2:8080';

// 真机 (WSL 局域网 IP)
// static const String apiBaseUrl = 'http://192.168.x.x:8080';
```

### 真机调试

WSL 获取局域网 IP: `hostname -I | awk '{print $1}'`

## 页面结构

```
lib/
├── main.dart                     # 入口 (Splash → Onboarding → Register → Main)
├── constants/
│   └── app_constants.dart        # 版本号、API 地址、超时配置
├── models/
│   ├── anchor.dart               # Anchor + Reaction + ContextHint 模型
│   ├── trace.dart                # 共鸣痕迹模型
│   └── user_identity.dart        # 匿名身份模型
├── screens/
│   ├── main_screen.dart          # 底部 Tab 导航 (遇见/记录/痕迹/我)
│   ├── onboarding_screen.dart    # 3 页引导
│   ├── register_screen.dart      # 昵称 + emoji 头像选择
│   ├── meet_screen.dart          # 遇见页 — 卡片式锚点浏览
│   ├── record_screen.dart        # 记录页 — 发布内容 + 反应历史
│   ├── trace_screen.dart         # 痕迹页 — 共鸣发现 + 知己区域
│   ├── me_screen.dart            # 我的页 — 个人信息 + 设置
│   ├── publish_screen.dart       # 发布页 — 创建新锚点
│   └── opinions_screen.dart      # 观点页 — 锚点下的反应列表
├── services/
│   ├── api_service.dart          # Dio HTTP 客户端 (自动 JWT + 401 重试)
│   └── storage_service.dart      # SharedPreferences 本地存储
└── widgets/
    ├── emotion_dialog.dart       # 情感词选择弹窗
    ├── nickname_generator.dart   # 随机昵称生成器
    ├── opinion_dialog.dart       # 观点输入弹窗
    └── reaction_buttons.dart     # 五态反应按钮组
```

## 核心流程

```
启动 → Splash (检查 onboarding + registration 状态)
  ├─ 未完成引导 → Onboarding (3 页滑动)
  ├─ 未注册 → Register (选昵称 + emoji)
  └─ 已注册 → Main (自动后台 API 认证)
       ├─ 遇见: 滑动卡片 → 选反应 → 可选写观点
       ├─ 记录: 查看已发布内容 + 反应统计
       ├─ 痕迹: 共鸣发现 + 知己区域
       └─ 我的: 个人信息 + 设置
```

## 设计规范

- **最低内容**: 100 字 (publish_screen)
- **设备指纹**: SHA-256, 64 字符 hex
- **API 超时**: 10 秒
- **分页**: 默认 20 条/页
- **反应历史**: 最多 100 条本地缓存
- **发布历史**: 最多 50 条本地缓存

## 已知限制

- 仅支持 Android (iOS/Web 未适配)
- 无离线支持
- 无推送通知
- 遇见页有轮询逻辑需要优化
