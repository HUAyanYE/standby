// ============================================================
// Standby Flutter-Rust Bridge — FFI API 定义
// ============================================================
//
// flutter_rust_bridge 从此文件自动生成:
// - Rust: 实际实现 (通过 gRPC 调用后端)
// - Dart: FFI 绑定 (供 Flutter UI 调用)
//
// 设计原则:
// - Dart 层不碰 AI 逻辑
// - 所有网络通信在 Rust 层完成
// - 原始传感器数据不离开设备
// ============================================================

// ============================================================
// 数据结构 (对齐 proto/common/common.proto)
// ============================================================

/// 设备类型
pub enum DeviceType {
    Phone,
    Tablet,
    Pc,
    Vehicle,
}

/// 反应类型
pub enum ReactionType {
    Resonance,      // 共鸣
    Neutral,        // 无感
    Opposition,     // 反对
    Unexperienced,  // 未体验
    Harmful,        // 有害
}

/// 情绪词
pub enum EmotionWord {
    None,
    Empathy,   // 同感
    Trigger,   // 触发
    Insight,   // 启发
    Shock,     // 震撼
}

/// 信任级别
pub enum TrustLevel {
    L0Browse,
    L1TraceVisible,
    L2OpinionReply,
    L3AsyncMessage,
    L4RealtimeChat,
    L5GroupChat,
}

/// 锚点摘要
pub struct AnchorSummary {
    pub anchor_id: String,
    pub title: String,
    pub anchor_type: String,
    pub topics: Vec<String>,
    pub total_reactions: u32,
}

/// 完整锚点
pub struct Anchor {
    pub anchor_id: String,
    pub text: String,
    pub anchor_type: String,
    pub topics: Vec<String>,
    pub source_attribution: String,
    pub quality_score: f64,
}

/// 匿名身份
pub struct AnonymousIdentity {
    pub identity_id: String,
    pub display_name: String,
    pub avatar_seed: String,
    pub anchor_id: String,
    pub is_fixed: bool,
}

/// 反应统计
pub struct ReactionSummary {
    pub anchor_id: String,
    pub resonance_count: u32,
    pub neutral_count: u32,
    pub opposition_count: u32,
    pub unexperienced_count: u32,
    pub harmful_count: u32,
    pub total_count: u32,
}

/// 群体记忆
pub struct GroupMemory {
    pub anchor_id: String,
    pub total_reactions: u32,
    pub resonance_count: u32,
    pub representative_opinions: Vec<RepresentativeOpinion>,
    pub user_has_history: bool,
}

pub struct RepresentativeOpinion {
    pub text: String,
    pub resonance_count: u32,
}

/// 重现锚点
pub struct ReplayAnchor {
    pub anchor_id: String,
    pub title: String,
    pub topics: Vec<String>,
    pub trigger_type: String,
    pub trigger_score: f64,
    pub group_memory: Option<GroupMemory>,
}

/// 反应视图
pub struct ReactionView {
    pub reaction_id: String,
    pub author_name: String,
    pub author_avatar_seed: String,
    pub reaction_type: ReactionType,
    pub emotion_word: EmotionWord,
    pub opinion_text: Option<String>,
    pub has_trace: bool,
    pub trace_hint: Option<String>,
}

/// 共鸣痕迹
pub struct ResonanceTrace {
    pub trace_id: String,
    pub other_user_name: String,
    pub other_user_avatar_seed: String,
    pub relationship_score: f64,
    pub shared_anchors: u32,
    pub shared_topics: u32,
    pub trust_level: TrustLevel,
}

/// 提交反应结果
pub struct SubmitReactionResult {
    pub success: bool,
    pub reaction_id: String,
    pub resonance_value: f64,
    pub resonance_count: u32,
    pub notification: Option<String>,
}

/// 用户档案
pub struct UserProfile {
    pub user_id: String,
    pub credit_score: f64,
    pub marker_credit: f64,
    pub total_reactions: u32,
    pub total_anchors_engaged: u32,
    pub confidant_count: u32,
}

/// 关系视图
pub struct RelationshipView {
    pub other_user_name: String,
    pub other_user_avatar_seed: String,
    pub relationship_score: f64,
    pub topic_diversity: u32,
    pub trust_level: TrustLevel,
    pub is_confidant: bool,
}

/// 知己视图
pub struct ConfidantView {
    pub confidant_id: String,
    pub fixed_name: String,
    pub fixed_avatar_url: String,
    pub relationship_score: f64,
}

/// 情境状态
pub struct ContextState {
    pub scene_type: String,
    pub mood_hint: String,
    pub attention_level: String,
    pub active_device: DeviceType,
}

/// 情境提示
pub struct ContextualHint {
    pub recommended_scene: String,
    pub mood_suggestion: String,
    pub topic_hints: Vec<String>,
}

/// 内容状态
pub struct ContentStatus {
    pub level: String,
    pub status_message: String,
    pub can_appeal: bool,
}

// ============================================================
// FFI API — 对应 standby_api.dart 中的接口
// ============================================================
//
// flutter_rust_bridge 会从这些函数签名自动生成:
// - Rust 侧: 实际实现 (gRPC 客户端调用)
// - Dart 侧: FFI 绑定
// ============================================================

// --- 认证 ---

/// 设备认证
pub fn device_auth(
    device_type: DeviceType,
    device_fingerprint: String,
    os_version: String,
    app_version: String,
) -> AuthResult {
    // TODO: 调用 API 网关 POST /auth/device
    todo!()
}

pub struct AuthResult {
    pub success: bool,
    pub access_token: Option<String>,
    pub refresh_token: Option<String>,
    pub expires_at: Option<u64>,
    pub error: Option<String>,
}

// --- 锚点 ---

/// 获取锚点列表
pub fn list_anchors(
    page: u32,
    page_size: u32,
    topic_filter: Vec<String>,
) -> Vec<AnchorSummary> {
    // TODO: 调用 API 网关 GET /anchors
    todo!()
}

/// 获取锚点详情
pub fn get_anchor(anchor_id: String) -> Option<Anchor> {
    // TODO: 调用 API 网关 GET /anchors/:id
    todo!()
}

/// 获取重现锚点
pub fn get_replay_anchors(top_k: u32) -> Vec<ReplayAnchor> {
    // TODO: 调用 API 网关 GET /anchors/replay
    todo!()
}

/// 导入锚点素材
pub fn import_anchor(content_text: String) -> ImportResult {
    // TODO: 调用 API 网关 POST /anchors/import
    todo!()
}

pub struct ImportResult {
    pub accepted: bool,
    pub anchor_id: Option<String>,
    pub message: String,
}

// --- 反应 ---

/// 提交反应
pub fn submit_reaction(
    anchor_id: String,
    reaction_type: ReactionType,
    emotion_word: EmotionWord,
    opinion_text: Option<String>,
) -> SubmitReactionResult {
    // TODO: 调用 API 网关 POST /reactions
    todo!()
}

/// 获取反应列表
pub fn list_reactions(
    anchor_id: String,
    filter_type: Option<ReactionType>,
    page: u32,
    page_size: u32,
) -> Vec<ReactionView> {
    // TODO: 调用 API 网关 GET /anchors/:id/reactions
    todo!()
}

/// 获取共鸣痕迹
pub fn get_resonance_traces(page: u32, page_size: u32) -> Vec<ResonanceTrace> {
    // TODO: 调用 API 网关 GET /traces
    todo!()
}

// --- 用户 ---

/// 获取用户档案
pub fn get_profile() -> UserProfile {
    // TODO: 调用 API 网关 GET /me
    todo!()
}

/// 获取关系列表
pub fn list_relationships(min_level: TrustLevel) -> Vec<RelationshipView> {
    // TODO: 调用 API 网关 GET /relationships
    todo!()
}

/// 表达知己意向
pub fn express_confidant_intent(target_hash: String) -> ConfidantIntentResult {
    // TODO: 调用 API 网关 POST /confidants/intent
    todo!()
}

pub struct ConfidantIntentResult {
    pub success: bool,
    pub matched: bool,
    pub message: String,
}

/// 获取知己列表
pub fn list_confidants() -> Vec<ConfidantView> {
    // TODO: 调用 API 网关 GET /confidants
    todo!()
}

// --- 情境 ---

/// 提交情境状态
pub fn submit_context_state(state: ContextState) {
    // 端侧融合, 只提交抽象状态
    // 原始传感器数据不离开设备
    // TODO: 调用 API 网关 POST /context
    todo!()
}

/// 获取情境提示
pub fn get_contextual_hint() -> ContextualHint {
    // TODO: 调用 API 网关 GET /context/hint
    todo!()
}

// --- 治理 ---

/// 举报内容
pub fn report_content(
    content_id: String,
    report_type: ReactionType,  // Harmful / Unexperienced
    reason: String,
) -> ReportResult {
    // TODO: 调用 API 网关 POST /report
    todo!()
}

pub struct ReportResult {
    pub accepted: bool,
    pub message: String,
}

/// 获取内容状态
pub fn get_content_status(content_id: String) -> ContentStatus {
    // TODO: 调用 API 网关 GET /content/:id/status
    todo!()
}

/// 申诉
pub fn appeal_decision(decision_id: String, reason: String) -> ReportResult {
    // TODO: 调用 API 网关 POST /appeal
    todo!()
}

// ============================================================
// 端侧特有能力 (不在 API 中, 纯端侧计算)
// ============================================================

/// 端侧文本编码 (用于预编码观点向量)
pub fn encode_text_device(text: String) -> Vec<f32> {
    // 使用端侧 BGE-small ONNX 模型
    // 返回 512 维 float32 向量
    todo!()
}

/// 设备指纹采集
pub fn collect_device_fingerprint() -> String {
    // 采集硬件特征, 返回 SHA-256 哈希
    // 原始数据不离开此函数
    todo!()
}

/// 端侧内容初筛 (治理引擎第一层)
pub fn content_quick_check(text: String) -> ContentCheckResult {
    // 关键词黑名单 + 轻量 ONNX 模型
    todo!()
}

pub enum ContentCheckResult {
    Pass,
    Suspect,
    Block,
}
