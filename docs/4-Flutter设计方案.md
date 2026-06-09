# Standby — Flutter 设计方案

> 基于产品理念的 Flutter 应用设计，遵循「无感的、融入生活的」设计原则。

---

## 一、设计哲学

### 1.1 核心设计原则

| 原则 | 含义 | Flutter 实现要点 |
|------|------|-----------------|
| **无感的、融入生活的** | 交互不刻意，不打断用户 flow | 动画平滑、转场自然、无弹窗打扰 |
| **真实 > 流量** | 不追求指标，追求真实表达 | 无点赞数、无排行榜、无关注数 |
| **先共享体验，再发现人** | 心物先行，关系后置 | 首页是心物流，不是人物流 |
| **渐进增强，非功能解锁** | 用户感知不到「解锁」，只感知到「越来越丰富」 | 无进度条、无成就系统、功能自然显现 |
| **匿名性永不打破** | 即使最深连接也只展示设定昵称/头像 | 无真名字段、无个人主页、无搜索用户 |

### 1.2 第一性原理

**Standby 的本质是什么？**

不是社交平台（不追求关系数量）
不是内容平台（不追求内容消费）
不是通讯工具（不追求即时通讯）

**是：让人重新敢于表达真实自我的安全空间。**

这意味着：
- 没有「粉丝数」「关注数」「点赞数」
- 没有「推荐算法」「热门排行」「流量分发」
- 没有「个人主页」「历史发言」「社交图谱」
- 只有：心物 → 感受 → 共鸣 → 连接

---

## 二、应用架构

### 2.1 技术栈

```
┌─────────────────────────────────────────────┐
│                   Flutter App                │
├─────────────────────────────────────────────┤
│  状态管理: Riverpod 2.0                      │
│  路由: GoRouter                              │
│  网络: Dio (REST via Gateway)                │
│  本地存储: SharedPreferences + SQLCipher      │
│  端侧 AI: ONNX Runtime (bge-small-zh 512d)  │
│  核心层: Rust FFI (flutter_rust_bridge)       │
└─────────────────────────────────────────────┘
```

**通信架构**：
- Flutter → API Gateway (Rust/Axum) → gRPC 引擎
- Gateway 负责协议转换（REST/JSON → gRPC），Flutter 端无需 gRPC 客户端
- 端侧 AI 推理通过 Rust FFI 调用 ONNX Runtime

**技术栈明细**：

| 层 | 技术选择 | 说明 |
|---|---------|------|
| UI 框架 | Flutter (Dart) | 跨平台 UI 框架，支持四端适配 |
| 状态管理 | Riverpod 2.0 | 响应式状态管理，代码生成 |
| 路由 | GoRouter | 声明式路由管理 |
| 网络 | Dio | HTTP 客户端，REST via Gateway |
| 本地存储 | SharedPreferences | 轻量级键值存储（用户设置、身份信息） |
| 加密存储 | SQLCipher | 端侧敏感数据加密存储（通过 Rust FFI） |
| 端侧 AI | ONNX Runtime | 轻量级端侧推理，BGE-small-zh 512 维 |
| 核心层 | Rust FFI | flutter_rust_bridge，类型安全的双向调用 |
| 文本编码 | BGE-small-zh-v1.5 | 端侧语义编码，512 维，单条延迟 ~200ms |

**端侧 AI 能力**：
- **BGE 文本编码**：将用户表达编码为 512 维语义向量
- **本地相似度计算**：端侧计算表达与心物的语义相似度
- **隐私保护**：编码过程在端侧完成，原始文本不上传

**状态管理说明**：
- 一期使用 Riverpod 2.0 进行状态管理
- 现有代码中的 StatefulWidget + setState 是原型阶段的临时方案
- 正式开发时统一使用 Riverpod，代码需要重构

**本地存储说明**：
- SharedPreferences：存储用户设置、身份信息、轻量级配置
- SQLCipher（通过 Rust FFI）：存储敏感数据（设备指纹、加密密钥等）
- Hive：一期不使用，二期可考虑用于离线缓存

### 2.2 目录结构

```
lib/
├── main.dart
├── app/
│   ├── app.dart                    # MaterialApp 配置
│   ├── router.dart                 # GoRouter 路由配置
│   └── theme.dart                  # 主题配置
├── core/
│   ├── constants/                  # 常量定义
│   ├── extensions/                 # 扩展方法
│   ├── utils/                      # 工具类
│   └── di/                         # 依赖注入
├── features/
│   ├── seedstone/                  # 心物模块（含感受链，感受链条目作为独立心物）
│   ├── resonance/                  # 共鸣模块
│   ├── record/                     # 记录模块
│   ├── profile/                    # 个人模块
│   └── confidant/                  # 知己模块
├── shared/
│   ├── widgets/                    # 共享组件
│   ├── models/                     # 共享模型
│   └── services/                   # 共享服务
└── l10n/                           # 国际化
```

---

## 三、页面结构

### 3.1 底部导航栏

```
┌─────────────────────────────────────────────────────────────┐
│                            状态栏                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                         页面内容                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│    遇见         记录         痕迹         我                │
└─────────────────────────────────────────────────────────────┘
```

**设计要点**：
- 底部导航栏四个 Tab：遇见 | 记录 | 痕迹 | 我
- 「遇见」Tab：心物流浏览，情境感知，共鸣交互
- 「记录」Tab：我的表达、我的共鸣
- 「痕迹」Tab：共鸣轨迹、关系脉络（渐进显现，关系深度光谱达到阈值后显现）
- 知己不是独立 Tab，入口在「我」页面内
- 导航栏使用 NavigationBar (Material 3)

### 3.2 页面清单

| 页面 | 路由 | 功能 | 显现条件 |
|------|------|------|---------|
| 遇见页 | `/meet` | 心物流、情境感知、共鸣交互 | 默认可用 |
| 记录页 | `/record` | 我的表达、我的共鸣 | 默认可用 |
| 痕迹页 | `/trace` | 共鸣轨迹、关系脉络、群体记忆 | 关系深度光谱达到阈值 |
| 我的页 | `/me` | 个人信息、设置、知己入口 | 默认可用 |
| 知己页 | `/confidant` | 感受知己列表、匿名知己 | 知己显现条件 |
| 心物详情 | `/seedstone/:id` | 心物内容、感受链 | 默认可用 |
| 发布页 | `/publish` | 发布心物/感想 | 默认可用 |

---

## 四、核心页面设计

### 4.1 遇见页

#### 感知链体现

**系统感知横幅**：
- 显示系统对用户当前状态的理解
- 例：「深夜 · 安静 · 适合深度阅读」
- 例：「午后 · 咖啡馆 · 适合轻松浏览」

**情境标签**：
- 心物卡片上显示情境相关信息
- 例：「🌧️ 窗外正在下雨」

#### 心物卡片组件

```dart
class SeedstoneCard extends StatelessWidget {
  final Seedstone seedstone;
  final ContextInfo? contextInfo;
  
  @override
  Widget build(BuildContext context) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      padding: EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: surfaceColor,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(),
          SizedBox(height: 16),
          Text(seedstone.title, style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
          SizedBox(height: 12),
          _buildContent(),
          if (contextInfo != null) ...[
            SizedBox(height: 16),
            _buildContextTag(),
          ],
          SizedBox(height: 20),
          _buildResonanceArea(),
        ],
      ),
    );
  }
}
```

#### 表达交互设计

用户不需要选择反应类型。用户只管表达，系统自动推断。

**用户界面**：
- 只有「写感想」的输入框
- 没有「共鸣」「反对」等按钮（系统后台自动推断五态反应）
- 提交后，系统自动推断共鸣度、深度、情绪词等

**系统内部（五态反应自动推断）**：
- 共鸣：表达与心物的情感方向一致，包含个人经历或真实细节
- 无感：表达简短且无情感倾向
- 反对：表达明确不认同，但包含理由（反对也是深度参与）
- 未体验：表达内容与心物无关或缺乏真实细节
- 有害：用户可主动标记，但必须写理由（有成本）

**情绪词细分（系统自动推断）**：
- 同感：「我也有同样的感受」
- 触发：「让我想起了……」
- 启发：「没这么想过，但你说得对」
- 震撼：「说不出话」

**设计原则**：用户只管表达，系统负责分类。五态反应是系统内部的统计指标，不是用户界面的功能。

```dart
class ResonanceArea extends StatefulWidget {
  final Seedstone seedstone;
  
  @override
  _ResonanceAreaState createState() => _ResonanceAreaState();
}

class _ResonanceAreaState extends State<ResonanceArea> {
  final TextEditingController _controller = TextEditingController();
  
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _buildFeelingChainPreview(), // 显示感受链条目摘要
        SizedBox(height: 12),
        _buildOpinionInput(),  // 写感受入口
      ],
    );
  }
  
  Widget _buildOpinionInput() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: surfaceColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _controller,
              decoration: InputDecoration(
                hintText: '写下你的感受...',
                border: InputBorder.none,
              ),
              maxLines: null,
            ),
          ),
          SizedBox(width: 8),
          _buildSubmitButton(),
        ],
      ),
    );
  }
}
```

### 4.2 记录页

**设计要点**：
- 分为「我的感想」和「我的共鸣」两个区域
- 显示回应的心物来源
- 显示共鸣人数和情绪词
- 无点赞数、无评论数、无分享数

### 4.3 我的页

**知己入口 - 渐进显现**：

```dart
class ConfidantEntry extends StatefulWidget {
  @override
  _ConfidantEntryState createState() => _ConfidantEntryState();
}

class _ConfidantEntryState extends State<ConfidantEntry> 
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<double> _sizeAnimation;
  
  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(milliseconds: 800),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
    _sizeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    final isVisible = ref.watch(confidantVisibleProvider);
    
    if (isVisible) {
      _controller.forward();
    }
    
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return SizeTransition(
          sizeFactor: _sizeAnimation,
          child: FadeTransition(
            opacity: _fadeAnimation,
            child: _buildMenuItem(),
          ),
        );
      },
    );
  }
}
```

### 4.4 知己页

**设计要点**：
- 匿名头像（emoji）
- 匿名昵称（「匿名用户」）
- 共鸣内容引用
- 共鸣标签（感受模式）
- 共鸣次数和模式匹配度
- 无真名、无真实头像、无个人主页

---

## 五、状态管理

### 5.1 Riverpod Providers

```dart
// 用户状态
@riverpod
class UserProfile extends _$UserProfile {
  @override
  UserProfileState build() {
    return UserProfileState.initial();
  }
}

// 心物状态
@riverpod
class SeedstoneList extends _$SeedstoneList {
  @override
  Future<List<Seedstone>> build() async {
    final repo = ref.read(seedstoneRepositoryProvider);
    return repo.getSeedstones();
  }
}

// 知己显现状态
@riverpod
class ConfidantVisible extends _$ConfidantVisible {
  @override
  bool build() {
    final relationships = ref.watch(relationshipDepthProvider);
    // 关系深度光谱（0-100）达到阈值时显现知己入口
    // 阈值计算是双向的——必须双方的共鸣关系分都达到阈值
    return relationships.any((r) => r.depthScore >= confidantDepthThreshold);
  }
}

// 关系深度（内部使用，不暴露给用户）
@riverpod
class RelationshipDepth extends _$RelationshipDepth {
  @override
  Map<String, double> build() {
    return {};
  }
}
```

### 5.2 感知链状态

```dart
// 情境感知状态
@riverpod
class ContextInfo extends _$ContextInfo {
  @override
  ContextState build() {
    return ContextState.initial();
  }
}

// 情境增强的心物列表
@riverpod
Future<List<ContextEnhancedSeedstone>> contextEnhancedSeedstones(
  ContextEnhancedSeedstonesRef ref,
) async {
  final seedstones = await ref.watch(seedstoneListProvider.future);
  final context = ref.watch(contextInfoProvider);
  
  return seedstones.map((seedstone) {
    return ContextEnhancedSeedstone(
      seedstone: seedstone,
      contextInfo: _enhanceWithContext(seedstone, context),
    );
  }).toList();
}
```

---

## 六、渐进显现机制

### 6.1 功能显现状态

```dart
enum FeatureType {
  confidant,      // 知己入口
  confidantChat,  // 匿名知己对话空间
}

@riverpod
class FeatureVisible extends _$FeatureVisible {
  @override
  bool build(FeatureType feature) {
    final relationships = ref.watch(relationshipDepthProvider);

    return switch (feature) {
      FeatureType.confidant =>
        relationships.any((r) => r.depthScore >= confidantDepthThreshold),
      FeatureType.confidantChat =>
        relationships.any((r) => r.hasMutualConfidant),
    };
  }
}
```

### 6.2 渐进显现组件

```dart
class FeatureGate extends ConsumerWidget {
  final FeatureType feature;
  final Widget child;
  final Widget? fallback;

  const FeatureGate({
    required this.feature,
    required this.child,
    this.fallback,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isVisible = ref.watch(featureVisibleProvider(feature));

    if (isVisible) {
      return child;
    }

    return fallback ?? SizedBox.shrink();
  }
}
```

---

## 七、设计规范

### 7.1 颜色系统

```dart
class StandbyColors {
  static const primary = Color(0xFFE74C3C);
  static const primarySoft = Color(0x26E74C3C);
  static const background = Color(0xFF0A0A0A);
  static const surface1 = Color(0xFF141414);
  static const surface2 = Color(0xFF1C1C1C);
  static const surface3 = Color(0xFF242424);
  static const text = Color(0xFFE8E8E8);
  static const text2 = Color(0xFF999999);
  static const text3 = Color(0xFF666666);
  static const border = Color(0x0FFFFFFF);
}
```

### 7.2 字体系统

```dart
class StandbyTextStyles {
  static const h1 = TextStyle(fontSize: 28, fontWeight: FontWeight.w600, letterSpacing: -0.5);
  static const h2 = TextStyle(fontSize: 22, fontWeight: FontWeight.w500);
  static const h3 = TextStyle(fontSize: 20, fontWeight: FontWeight.w600, letterSpacing: -0.3);
  static const body = TextStyle(fontSize: 15, fontWeight: FontWeight.w400, height: 1.8);
  static const label = TextStyle(fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1.5);
  static const button = TextStyle(fontSize: 14, fontWeight: FontWeight.w500);
}
```

### 7.3 间距系统

```dart
class StandbySpacing {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
  static const pagePadding = EdgeInsets.all(20);
  static const cardPadding = EdgeInsets.all(24);
  static const cardGap = 16.0;
}
```

### 7.4 圆角系统

```dart
class StandbyRadius {
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 20.0;
  static const xxl = 24.0;
  static final cardRadius = BorderRadius.circular(xl);
  static final buttonRadius = BorderRadius.circular(md);
  static final tagRadius = BorderRadius.circular(sm);
}
```

---

## 八、动画规范

### 8.1 动画原则

1. **平滑自然**：使用 easeOut 曲线，避免生硬
2. **有意义**：动画应该传达状态变化，不是装饰
3. **不打断**：动画不应该打断用户 flow
4. **可选**：尊重用户的减少动画偏好

### 8.2 动画时长

```dart
class StandbyDuration {
  static const fast = Duration(milliseconds: 200);
  static const normal = Duration(milliseconds: 300);
  static const slow = Duration(milliseconds: 500);
  static const verySlow = Duration(milliseconds: 800);
}
```

---

## 九、实现优先级

### P0（一期必须有）

- 心物卡片组件
- 表达输入交互
- 共鸣计数显示
- 记录页面
- 我的页面
- 知己入口（渐进显现）
- 知己页面

### P1（尽快做）

- 感知链横幅
- 情境标签
- 关系深度算法
- 静默机制
- 跨设备场景接力

### P2（可以后做）

- 多设备融合感知
- 高级动画效果
- 无障碍支持

---

## 十、系统级输入设计

> **设计原则**：「无感的、融入生活的」——交互不刻意，不打断用户 flow。系统级输入让表达变得自然，不需要"打开 App"才能感受和表达。

### 10.1 Android Widget

**心物每日推荐 Widget**：
- 每天推送一个心物到桌面 Widget
- 用户无需打开 App 即可看到
- 点击 Widget 直接进入心物详情页
- 设计风格：简洁、安静、不打扰

### 10.2 通知系统

**共鸣发现通知**：
- 当系统发现新的共鸣关系时，发送通知
- 通知内容：「有个人总是跟你有同样的感受」
- 不显示对方身份，只提示存在
- 用户点击通知进入知己页面

**心物重现通知**：
- 当心物随时间回归（季节性、周年）时，发送通知
- 通知内容：「一年前的今天，你在这个心物下留下了感想」
- 点击进入心物详情，查看群体记忆

**情境推送通知**：
- 基于用户生活节奏，在合适的时间推送心物
- 例：深夜推送安静的心物，早晨推送激励的心物
- 用户可关闭此功能

### 10.3 系统分享 Intent

**外部内容 → 心物素材**：
- 用户在其他 App 看到深度文章、视频、图片
- 通过系统分享直接导入 Standby 作为心物素材
- 系统自动提取关键信息，生成心物草稿
- 用户确认后发布

**支持的分享类型**：
- 文字：直接导入
- 图片：导入并添加描述
- 视频链接：提取关键帧和描述
- 网页链接：提取标题和摘要

### 10.4 语音输入

**语音感想**：
- 用户可以通过语音记录感受
- 系统自动转文字，保留语音作为附件
- 适用于开车、走路等场景

**语音触发心物**：
- 用户说"帮我记一下"，系统关联当前上下文
- 正在听的歌、正在看的视频、正在经过的地方
- 自动生成心物草稿

### 10.5 实现优先级

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 系统分享 Intent | P1 | 一期实现，降低表达门槛 |
| 通知系统 | P1 | 一期实现，核心体验 |
| Android Widget | P2 | 二期实现，增强系统级体验 |
| 语音输入 | P2 | 二期实现，多模态表达 |

---

## 七、构建与配置

### 7.1 快速启动

```bash
# 从 WSL 调用 Windows Flutter SDK
cd /mnt/d/Hermes/standby/standby_app
cmd.exe /c "flutter pub get"
cmd.exe /c "flutter build apk --release"
```

### 7.2 安装

```bash
# 模拟器
cmd.exe /c "flutter install --device-id emulator-5554"

# 真机
cmd.exe /c "flutter install --device-id <设备ID>"
```

### 7.3 API 地址配置

`lib/constants/app_constants.dart` 中的 `apiBaseUrl`:

```dart
// Android 模拟器 (本机)
static const String apiBaseUrl = 'http://10.0.2.2:8080';

// 真机 (WSL 局域网 IP)
// static const String apiBaseUrl = 'http://192.168.x.x:8080';
```

WSL 获取局域网 IP: `hostname -I | awk '{print $1}'`

### 7.4 版本号规范

版本号格式：`主版本.次版本.补丁版本+构建号`（如 v0.2.0+2）

版本号集中管理在 `constants/app_constants.dart`，禁止硬编码。

### 7.5 核心流程

```
启动 → Splash (检查 onboarding + registration 状态)
  ├─ 未完成引导 → Onboarding (3 页滑动)
  ├─ 未注册 → Register (选昵称 + emoji)
  └─ 已注册 → Main (自动后台 API 认证)
       ├─ 发现: 心物流 → 写感想 → 系统推断共鸣
       ├─ 记录: 我的感想 + 我的共鸣
       └─ 我的: 个人信息 + 设置 + 知己入口(渐进显现)
```

### 7.6 设计规范数值

- **最低内容**: 100 字 (发布心物)
- **设备指纹**: SHA-256, 64 字符 hex
- **API 超时**: 10 秒
- **分页**: 默认 20 条/页

---

*文档版本：v2.0*
*创建日期：2026-04-30*
*整合自 Flutter 设计方案 v1.0 + standby_app README*
