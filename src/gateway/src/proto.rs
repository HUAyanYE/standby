// Proto 生成的类型和 gRPC 客户端
// 由 tonic-build 在 build.rs 中自动生成

pub mod common {
    tonic::include_proto!("standby.common");
}

pub mod engines {
    tonic::include_proto!("standby.engines");

    // 重导出常用客户端
    pub use anchor_engine_client::AnchorEngineClient;
    pub use context_engine_client::ContextEngineClient;
    pub use governance_engine_client::GovernanceEngineClient;
    pub use resonance_engine_client::ResonanceEngineClient;
    pub use user_engine_client::UserEngineClient;
}
