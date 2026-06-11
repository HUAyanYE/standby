use tonic::transport::Channel;

use crate::error::ApiError;
use crate::proto::engines::context_engine_client::ContextEngineClient;
use crate::models::context::*;

pub struct ContextClient {
    inner: ContextEngineClient<Channel>,
}

impl Clone for ContextClient {
    fn clone(&self) -> Self {
        Self {
            inner: self.inner.clone(),
        }
    }
}

impl ContextClient {
    pub async fn new(url: &str) -> anyhow::Result<Self> {
        let inner = ContextEngineClient::connect(url.to_string()).await?;
        Ok(Self { inner })
    }

    pub async fn check_health(&mut self) -> bool {
        let req = tonic::Request::new(super::super::proto::engines::GetContextualWeightsRequest {
            user_id: String::new(),
            candidate_topics: vec![],
        });
        self.inner.get_contextual_weights(req).await.is_ok()
    }

    pub async fn submit_context(
        &mut self,
        user_id: &str,
        req: SubmitContextRequest,
    ) -> Result<bool, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::SubmitContextStateRequest {
            user_id: user_id.to_string(),
            scene_type: req.scene_type,
            mood_hint: req.mood_hint.unwrap_or_default(),
            attention_level: req.attention_level.unwrap_or_default(),
            active_device: req.active_device.unwrap_or(0),
            timestamp: chrono::Utc::now().timestamp(),
        });

        let response = self.inner.submit_context_state(request).await?.into_inner();
        Ok(response.accepted)
    }

    pub async fn get_contextual_weights(
        &mut self,
        user_id: &str,
        topics: Vec<String>,
    ) -> Result<ContextualWeights, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::GetContextualWeightsRequest {
            user_id: user_id.to_string(),
            candidate_topics: topics,
        });

        let response = self.inner.get_contextual_weights(request).await?.into_inner();

        Ok(ContextualWeights {
            topic_weights: response.topic_weights,
            recommended_scene: response.recommended_scene,
        })
    }
}
