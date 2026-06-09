pub mod anchor;
pub mod resonance;
pub mod governance;
pub mod context;

use std::sync::Arc;

/// 聚合所有引擎客户端
#[derive(Clone)]
pub struct EngineClients {
    pub anchor: Arc<anchor::AnchorClient>,
    pub resonance: Arc<resonance::ResonanceClient>,
    pub governance: Arc<governance::GovernanceClient>,
    pub context: Arc<context::ContextClient>,
}

impl EngineClients {
    pub async fn new(
        anchor_url: &str,
        resonance_url: &str,
        governance_url: &str,
        context_url: &str,
    ) -> anyhow::Result<Self> {
        Ok(Self {
            anchor: Arc::new(anchor::AnchorClient::new(anchor_url).await?),
            resonance: Arc::new(resonance::ResonanceClient::new(resonance_url).await?),
            governance: Arc::new(governance::GovernanceClient::new(governance_url).await?),
            context: Arc::new(context::ContextClient::new(context_url).await?),
        })
    }
}
