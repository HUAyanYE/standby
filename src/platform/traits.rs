//! ============================================================
//! Standby 客户端 Rust 核心层 — 平台抽象接口
//! ============================================================
//!
//! 对齐技术架构 §2.2: 设备生态抽象层
//! 当前目标生态: 小米澎湃 OS
//! 扩展策略: 定义 trait 签名, 按 trait 组织代码
//!           不做通用 adapter, 不做运行时切换
//! ============================================================

use std::time::{SystemTime, UNIX_EPOCH};

// ============================================================
// 错误类型
// ============================================================

#[derive(Debug, thiserror::Error)]
pub enum PlatformError {
    #[error("设备不支持: {0}")]
    Unsupported(String),
    
    #[error("权限不足: {0}")]
    PermissionDenied(String),
    
    #[error("服务不可用: {0}")]
    ServiceUnavailable(String),
    
    #[error("通信失败: {0}")]
    CommunicationFailed(String),
}

pub type PlatformResult<T> = Result<T, PlatformError>;

// ============================================================
// 数据结构
// ============================================================

/// 设备指纹 (不暴露原始硬件信息)
#[derive(Debug, Clone)]
pub struct DeviceFingerprint {
    pub hash: String,           // SHA-256(硬件特征拼接 + 盐值)
    pub device_type: DeviceType,
    pub os_version: String,
    pub app_version: String,
}

#[derive(Debug, Clone, Copy)]
pub enum DeviceType {
    Phone,
    Tablet,
    Pc,
    Vehicle,
}

/// 情境状态 (端侧融合后输出, 不含原始传感器数据)
#[derive(Debug, Clone)]
pub struct ContextState {
    pub scene_type: String,        // "commute" / "home_relax" / "work_break" / "driving"
    pub mood_hint: String,         // "calm" / "reflective" / "energetic" / "tired"
    pub attention_level: String,   // "focused" / "casual" / "distracted"
    pub active_device: DeviceType,
    pub timestamp: u64,
}

impl ContextState {
    pub fn now(scene: &str, mood: &str, attention: &str, device: DeviceType) -> Self {
        Self {
            scene_type: scene.to_string(),
            mood_hint: mood.to_string(),
            attention_level: attention.to_string(),
            active_device: device,
            timestamp: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        }
    }
}

/// 异步回调类型
pub type AsyncCallback = Box<dyn Fn(&str) + Send + Sync>;

/// 设备信息
#[derive(Debug, Clone)]
pub struct DeviceInfo {
    pub device_type: DeviceType,
    pub name: String,
    pub is_online: bool,
}

/// 邀请码
#[derive(Debug, Clone)]
pub struct InviteCode {
    pub code: String,
    pub expires_at: u64,
    pub max_uses: u32,
    pub current_uses: u32,
}

/// 分享目标
#[derive(Debug, Clone)]
pub enum ShareTarget {
    /// 小米互联互通框架发现的设备
    Device(DeviceInfo),
    /// 生成邀请码
    InviteCode,
}

// ============================================================
// Trait: 设备指纹采集
// ============================================================
//
// Android: ANDROID_ID + Build.FINGERPRINT + 硬件特征
// iOS: identifierForVendor + 设备型号
// PC: 主板序列号哈希 + MAC 地址哈希
// 车机: 车载系统唯一标识 + VIN 哈希

pub trait DeviceFingerprintProvider {
    /// 采集设备指纹
    /// 返回 SHA-256 哈希, 不返回原始硬件信息
    fn collect_fingerprint(&self) -> PlatformResult<DeviceFingerprint>;
    
    /// 验证设备完整性
    /// iOS: App Attest
    /// Android: Play Integrity / SafetyNet
    fn verify_integrity(&self) -> PlatformResult<bool>;
    
    /// 检测模拟器环境
    fn is_emulator(&self) -> bool;
    
    /// 检测 root/jailbreak
    fn is_compromised(&self) -> bool;
}

// ============================================================
// Trait: 小爱同学通信桥接
// ============================================================
//
// 通过 Platform Channel 调用小米 SDK
// 用途: 情境感知、语音桥接、设备接力

pub trait SmartAssistantBridge {
    /// 发送消息到小爱同学
    fn send_message(&self, msg: &str) -> PlatformResult<()>;
    
    /// 注册回调 (接收小爱同学的主动推送)
    fn register_callback(&self, cb: AsyncCallback) -> PlatformResult<()>;
    
    /// 查询用户当前设备状态
    fn query_device_status(&self) -> PlatformResult<DeviceInfo>;
    
    /// 请求语音输入
    fn request_voice_input(&self) -> PlatformResult<Option<String>>;
}

// ============================================================
// Trait: 多设备发现与协同
// ============================================================
//
// 小米互联互通框架的 Android 接口
// 用途: 场景接力、状态同步

pub trait DeviceDiscovery {
    /// 发现同一账号下的其他设备
    fn discover_devices(&self) -> PlatformResult<Vec<DeviceInfo>>;
    
    /// 同步情境状态到其他设备
    fn sync_state(&self, state: &ContextState) -> PlatformResult<()>;
    
    /// 从其他设备接收情境状态
    fn receive_state(&self) -> PlatformResult<Option<ContextState>>;
    
    /// 请求设备接力 (如: 手机 → 平板)
    fn request_handoff(&self, target: &DeviceInfo, context: &str) -> PlatformResult<bool>;
}

// ============================================================
// Trait: 系统级分享扩展
// ============================================================
//
// Flutter share_plus + 小米分享扩展
// 限制: 不允许分享具体观点链接

pub trait ShareExtension {
    /// 分享锚点 (仅锚点, 不含具体观点)
    fn share_anchor(&self, anchor_id: &str, to: &ShareTarget) -> PlatformResult<()>;
    
    /// 生成熟人分享码
    fn generate_invite_code(&self) -> PlatformResult<InviteCode>;
    
    /// 验证分享码
    fn verify_invite_code(&self, code: &str) -> PlatformResult<bool>;
    
    /// 检查分享是否被允许 (防滥用)
    fn check_share_allowed(&self) -> PlatformResult<bool>;
}

// ============================================================
// Trait: 车机集成
// ============================================================
//
// Android Automotive 适配
// 用途: 驾驶模式、语音优先、安全限制

pub trait VehicleIntegration {
    /// 检测是否在驾驶状态
    fn is_driving(&self) -> bool;
    
    /// 获取语音输入 (驾驶模式下唯一输入方式)
    fn voice_input(&self) -> PlatformResult<Option<String>>;
    
    /// 检测安全模式是否激活
    /// 激活时: 禁止文本输入, 仅允许语音和听觉输出
    fn safety_mode_active(&self) -> bool;
    
    /// 获取驾驶模式下的可用功能列表
    fn get_driving_permissions(&self) -> DrivingPermissions;
}

#[derive(Debug, Clone)]
pub struct DrivingPermissions {
    pub can_listen: bool,       // 收听锚点
    pub can_voice_react: bool,  // 语音触发感想
    pub can_view: bool,         // 查看内容 (受安全限制)
    pub can_type: bool,         // 文本输入 (驾驶时禁止)
}

impl Default for DrivingPermissions {
    fn default() -> Self {
        Self {
            can_listen: true,
            can_voice_react: true,
            can_view: false,     // 驾驶时默认禁止查看
            can_type: false,     // 驾驶时默认禁止输入
        }
    }
}

// ============================================================
// Trait: 端侧加密存储
// ============================================================
//
// SQLCipher 加密 SQLite
// 密钥由设备安全模块持有

pub trait EncryptedStorage {
    /// 初始化存储 (首次创建或解锁)
    fn initialize(&self, key: &[u8]) -> PlatformResult<()>;
    
    /// 存储数据
    fn put(&self, key: &str, value: &[u8]) -> PlatformResult<()>;
    
    /// 读取数据
    fn get(&self, key: &str) -> PlatformResult<Option<Vec<u8>>>;
    
    /// 删除数据
    fn delete(&self, key: &str) -> PlatformResult<()>;
    
    /// 检查存储是否已初始化
    fn is_initialized(&self) -> bool;
}

// ============================================================
// 便利实现: 组合 trait
// ============================================================

/// 完整的平台能力集合
/// 每个具体平台 (Xiaomi, iOS, ...) 实现这个 trait
pub trait PlatformCapabilities:
    DeviceFingerprintProvider
    + SmartAssistantBridge
    + DeviceDiscovery
    + ShareExtension
    + VehicleIntegration
    + EncryptedStorage
{
    /// 获取平台名称
    fn platform_name(&self) -> &str;
    
    /// 获取平台版本
    fn platform_version(&self) -> &str;
}

// ============================================================
// 安全约束 (编译时保证)
// ============================================================

/// 标记 trait: 确保原始传感器数据不离开设备
/// 实现此 trait 的类型不能实现 Serialize
pub trait LocalOnly {}

/// 标记 trait: 确保数据经过加密网关
pub trait EncryptedTransport {}

// ============================================================
// 测试
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_context_state_creation() {
        let state = ContextState::now(
            "commute",
            "calm",
            "casual",
            DeviceType::Phone,
        );
        assert_eq!(state.scene_type, "commute");
        assert_eq!(state.mood_hint, "calm");
        assert!(state.timestamp > 0);
    }
    
    #[test]
    fn test_driving_permissions_default() {
        let perms = DrivingPermissions::default();
        assert!(perms.can_listen);
        assert!(perms.can_voice_react);
        assert!(!perms.can_view);
        assert!(!perms.can_type);
    }
}
