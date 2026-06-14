use std::time::Duration;
use tonic::transport::Channel;

use crate::error::ApiError;
use crate::proto::engines::anchor_engine_client::AnchorEngineClient;
use crate::models::anchor::*;
use super::retry::{RetryConfig, with_retry, with_timeout};

pub struct AnchorClient {
    inner: AnchorEngineClient<Channel>,
    retry_config: RetryConfig,
    timeout: Duration,
}

impl Clone for AnchorClient {
    fn clone(&self) -> Self {
        Self {
            inner: self.inner.clone(),
            retry_config: RetryConfig::default(),
            timeout: Duration::from_secs(10),
        }
    }
}

impl AnchorClient {
    pub async fn new(url: &str) -> anyhow::Result<Self> {
        let inner = AnchorEngineClient::connect(url.to_string()).await?;
        Ok(Self {
            inner,
            retry_config: RetryConfig::default(),
            timeout: Duration::from_secs(10),
        })
    }

    pub async fn check_health(&self) -> bool {
        let mut inner = self.inner.clone();
        let req = tonic::Request::new(super::super::proto::engines::ListAnchorsRequest {
            page: 1,
            page_size: 1,
            topic_filter: String::new(),
        });
        // 健康检查使用短超时，不重试
        match tokio::time::timeout(Duration::from_secs(3), inner.list_anchors(req)).await {
            Ok(Ok(_)) => true,
            _ => false,
        }
    }

    pub async fn generate_anchor(
        &mut self,
        req: GenerateAnchorRequest,
    ) -> Result<(String, f32), ApiError> {
        let inner = &mut self.inner;
        let timeout = self.timeout;
        let request = tonic::Request::new(super::super::proto::engines::GenerateAnchorRequest {
            source_texts: req.source_texts,
            topic_hints: req.topic_hints.unwrap_or_default(),
            source: req.source.unwrap_or_else(|| "user".into()),
            modality: req.modality.unwrap_or_else(|| "text".into()),
        });

        let response = with_timeout(timeout, "generate_anchor", || async {
            inner.generate_anchor(request.clone()).await
        }).await?;

        let resp = response.into_inner();
        if resp.success {
            Ok((resp.anchor_id, resp.quality_score))
        } else {
            Err(ApiError::BadRequest(resp.rejection_reason))
        }
    }

    pub async fn list_anchors(
        &mut self,
        params: PaginationParams,
    ) -> Result<(Vec<AnchorSummary>, i32, bool), ApiError> {
        let inner = &mut self.inner;
        let retry_config = &self.retry_config;
        let timeout = self.timeout;

        let request = tonic::Request::new(super::super::proto::engines::ListAnchorsRequest {
            page: params.page.unwrap_or(1) as i32,
            page_size: params.page_size.unwrap_or(20) as i32,
            topic_filter: params.topic_filter.unwrap_or_default(),
        });

        let response = with_retry(retry_config, "list_anchors", || {
            let req = request.clone();
            let client = inner.clone();
            async move { client.list_anchors(req).await }
        }).await?;

        let resp = response.into_inner();
        let anchors = resp
            .anchors
            .into_iter()
            .map(|a| AnchorSummary {
                anchor_id: a.anchor_id,
                text: a.text,
                topics: a.topics,
                quality_score: a.quality_score,
                reaction_count: a.reaction_count,
                created_at: a.created_at,
            })
            .collect();

        Ok((anchors, resp.total_count, resp.has_more))
    }

    pub async fn get_anchor_metadata(
        &mut self,
        anchor_id: &str,
    ) -> Result<AnchorDetail, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::GetAnchorMetadataRequest {
            anchor_id: anchor_id.to_string(),
        });

        let response = self.inner.get_anchor_metadata(request).await?.into_inner();

        if response.found {
            Ok(AnchorDetail {
                anchor_id: response.anchor_id,
                text: response.text,
                topics: response.topics,
                quality_score: response.quality_score,
                created_at: response.created_at,
            })
        } else {
            Err(ApiError::NotFound(format!("锚点 {} 不存在", anchor_id)))
        }
    }

    pub async fn get_group_memory(
        &mut self,
        anchor_id: &str,
        user_id: &str,
    ) -> Result<GroupMemory, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::GetGroupMemoryRequest {
            anchor_id: anchor_id.to_string(),
            user_id: user_id.to_string(),
        });

        let response = self.inner.get_group_memory(request).await?.into_inner();

        Ok(GroupMemory {
            user_opinion_text: response.user_opinion_text,
            resonance_count_at_time: response.resonance_count_at_time,
            emotion_words: response.emotion_words,
            group_evolution: response.group_evolution,
        })
    }

    pub async fn get_feeling_chain(
        &mut self,
        anchor_id: &str,
        max_depth: i32,
    ) -> Result<Vec<FeelingChainNode>, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::GetFeelingChainRequest {
            anchor_id: anchor_id.to_string(),
            max_depth,
        });

        let response = self.inner.get_feeling_chain(request).await?.into_inner();

        if !response.found {
            return Ok(vec![]);
        }

        let nodes = response
            .nodes
            .into_iter()
            .map(|n| FeelingChainNode {
                reaction_id: n.reaction_id,
                user_id: n.user_id,
                display_name: n.display_name,
                avatar_seed: n.avatar_seed,
                text_content: n.text_content,
                emotion_word: n.emotion_word,
                parent_reaction_id: n.parent_reaction_id,
                depth: n.depth,
                created_at: n.created_at,
            })
            .collect();

        Ok(nodes)
    }
}
