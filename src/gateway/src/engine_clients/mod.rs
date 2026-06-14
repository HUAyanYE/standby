pub mod anchor;
pub mod resonance;
pub mod governance;
pub mod context;
pub mod retry;

use std::sync::Arc;

/// 聚合所有引擎客户端
#[derive(Clone)]
pub struct EngineClients {
    pub(crate) anchor: Arc<anchor::AnchorClient>,
    pub(crate) resonance: Arc<resonance::ResonanceClient>,
    pub(crate) governance: Arc<governance::GovernanceClient>,
    pub(crate) context: Arc<context::ContextClient>,
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
