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
| **渐进增强，非功能解锁** | 用户感知不到「解锁」，只感知到「越来越丰富」 | 无进度条、无成就系统、功能自然涌现 |
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
│  网络: Dio + WebSocket                       │
│  本地存储: Hive + SharedPreferences           │
│  端侧 AI: TensorFlow Lite / ONNX Runtime    │
└─────────────────────────────────────────────┘
```

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
│   ├── seedstone/                     # 心物模块
│   ├── resonance/                  # 共鸣模块
│   ├── record/                     # 记录模块
│   ├── profile/                    # 个人模块
│   ├── confidant/                  # 知己模块
│   └── perception/                 # 感知链模块
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
┌─────────────────────────────────────────────┐
│                    状态栏                     │
├─────────────────────────────────────────────┤
│                                             │
│                   页面内容                   │
│                                             │
├─────────────────────────────────────────────┤
│   发现        记录        我                 │
└─────────────────────────────────────────────┘
```

**设计要点**：
- 底部导航栏始终三个 Tab：发现 | 记录 | 我
- 知己不是独立 Tab，入口在「我」页面内
- 导航栏使用 NavigationBar (Material 3)

### 3.2 页面清单

| 页面 | 路由 | 功能 |
|------|------|------|
| 发现页 | `/discover` | 心物流、情境感知、共鸣交互 |
| 记录页 | `/record` | 我的表达、我的共鸣 |
| 我的页 | `/profile` | 个人信息、设置、知己入口 |
| 知己页 | `/confidant` | 感受知己列表、匿名知己 |
| 心物详情 | `/seedstone/:id` | 心物内容、感受链 |

---

## 四、核心页面设计

### 4.1 发现页

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
- 没有「共鸣」「反对」等按钮
- 提交后，系统自动推断共鸣度、深度、情绪词等

**系统内部**：
- 共鸣度：表达与心物的情感方向是否一致
- 深度：表达是否有真实细节和个人经历
- 相关性：表达是否与心物相关
- 情绪词：同感/触发/启发/震撼
- 有害性：是否恶意/虚假/有害（用户可主动标记，需写理由）

```dart
class ResonanceArea extends StatefulWidget {
  final Seedstone seedstone;
  
  @override
  _ResonanceAreaState createState() => _ResonanceAreaState();
}

class _ResonanceAreaState extends State<ResonanceArea> {
  bool isResonated = false;
  
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _buildResonanceCount(),
        SizedBox(height: 12),
        _buildResonateButton(),
        SizedBox(height: 12),
        _buildSecondaryReactions(),
      ],
    );
  }
  
  Widget _buildResonateButton() {
    return GestureDetector(
      onTap: () => _toggleResonance(),
      child: AnimatedContainer(
        duration: Duration(milliseconds: 300),
        padding: EdgeInsets.symmetric(vertical: 14, horizontal: 20),
        decoration: BoxDecoration(
          color: isResonated ? primaryColor.withOpacity(0.15) : Colors.transparent,
          border: Border.all(
            color: isResonated ? primaryColor.withOpacity(0.3) : borderColor,
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('💫', style: TextStyle(fontSize: 18)),
            SizedBox(width: 8),
            Text(isResonated ? '已共鸣' : '共鸣'),
          ],
        ),
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

**知己入口 - 渐进解锁**：

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
    final isUnlocked = ref.watch(confidantUnlockProvider);
    
    if (isUnlocked) {
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

// 知己解锁状态
@riverpod
class ConfidantUnlock extends _$ConfidantUnlock {
  @override
  bool build() {
    final resonanceData = ref.watch(resonanceDataProvider);
    return resonanceData.deepResonanceCount >= 1;
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

## 六、渐进解锁机制

### 6.1 功能解锁状态

```dart
enum FeatureType {
  confidant,      // 知己入口
  confidantChat,  // 匿名知己聊天
  offlineMeet,    // 线下见面
}

@riverpod
class FeatureUnlock extends _$FeatureUnlock {
  @override
  bool build(FeatureType feature) {
    final resonanceData = ref.watch(resonanceDataProvider);
    
    return switch (feature) {
      FeatureType.confidant =>
        resonanceData.deepResonanceCount >= 1,
      FeatureType.confidantChat =>
        resonanceData.hasMutualConfidant,
      FeatureType.offlineMeet =>
        resonanceData.confidantDepth >= 0.8 &&
        resonanceData.confidantStability >= 0.7,
    };
  }
}
```

### 6.2 渐进解锁组件

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
    final isUnlocked = ref.watch(featureUnlockProvider(feature));
    
    if (isUnlocked) {
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
- 知己入口（渐进解锁）
- 知己页面

### P1（尽快做）

- 感知链横幅
- 情境标签
- 关系深度算法
- 静默机制
- 跨设备场景接力

### P2（可以后做）

- 多设备融合感知
- 线下见面功能
- 高级动画效果
- 无障碍支持

---

*文档版本：v1.0*
*创建日期：2026-04-27*
*基于 FLUTTER-DESIGN v0.1 整理*
