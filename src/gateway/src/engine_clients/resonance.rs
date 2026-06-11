use tonic::transport::Channel;

use crate::error::ApiError;
use crate::proto::engines::resonance_engine_client::ResonanceEngineClient;
use crate::models::reaction::*;
use crate::models::context::EncodeTextResponse;

pub struct ResonanceClient {
    inner: ResonanceEngineClient<Channel>,
}

impl Clone for ResonanceClient {
    fn clone(&self) -> Self {
        Self {
            inner: self.inner.clone(),
        }
    }
}

impl ResonanceClient {
    pub async fn new(url: &str) -> anyhow::Result<Self> {
        let inner = ResonanceEngineClient::connect(url.to_string()).await?;
        Ok(Self { inner })
    }

    pub async fn check_health(&self) -> bool {
        let mut inner = self.inner.clone();
        let req = tonic::Request::new(super::super::proto::engines::ListReactionsRequest {
            anchor_id: String::new(),
            page: 1,
            page_size: 1,
            filter_type: String::new(),
        });
        inner.list_reactions(req).await.is_ok()
    }

    pub async fn process_reaction(
        &mut self,
        user_id: &str,
        req: ProcessReactionRequest,
    ) -> Result<ReactionResult, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::ProcessReactionRequest {
            anchor_id: req.anchor_id,
            user_id: user_id.to_string(),
            reaction_type: req.reaction_type,
            opinion_text: req.opinion_text.unwrap_or_default(),
            opinion_vector: req.opinion_vector.unwrap_or_default(),
            emotion_word: req.emotion_word.unwrap_or(0),
            timestamp: chrono::Utc::now().timestamp(),
            event_id: uuid::Uuid::new_v4().to_string(),
            parent_reaction_id: req.parent_reaction_id.unwrap_or_default(),
        });

        let response = self.inner.process_reaction(request).await?.into_inner();

        Ok(ReactionResult {
            success: response.success,
            event_id: response.event_id,
            resonance_value: response.resonance_value,
            relationship_score: response.relationship_score,
            related_user_id: response.related_user_id,
            processing_time_ms: response.processing_time_ms,
        })
    }

    pub async fn process_batch(
        &mut self,
        user_id: &str,
        req: ProcessBatchRequest,
    ) -> Result<BatchResult, ApiError> {
        let reactions = req
            .reactions
            .into_iter()
            .map(|r| super::super::proto::engines::ProcessReactionRequest {
                anchor_id: r.anchor_id,
                user_id: user_id.to_string(),
                reaction_type: r.reaction_type,
                opinion_text: r.opinion_text.unwrap_or_default(),
                opinion_vector: r.opinion_vector.unwrap_or_default(),
                emotion_word: r.emotion_word.unwrap_or(0),
                timestamp: chrono::Utc::now().timestamp(),
                event_id: uuid::Uuid::new_v4().to_string(),
                parent_reaction_id: r.parent_reaction_id.unwrap_or_default(),
            })
            .collect();

        let request = tonic::Request::new(super::super::proto::engines::ProcessBatchRequest {
            batch_id: req.batch_id,
            reactions,
        });

        let response = self.inner.process_batch(request).await?.into_inner();

        Ok(BatchResult {
            success: response.success,
            batch_id: response.batch_id,
            total_processed: response.total_processed,
            total_errors: response.total_errors,
        })
    }

    pub async fn list_reactions(
        &mut self,
        anchor_id: &str,
        params: ReactionListParams,
    ) -> Result<(Vec<ReactionItem>, i32, bool), ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::ListReactionsRequest {
            anchor_id: anchor_id.to_string(),
            page: params.page.unwrap_or(1) as i32,
            page_size: params.page_size.unwrap_or(20) as i32,
            filter_type: params.filter_type.unwrap_or_default(),
        });

        let response = self.inner.list_reactions(request).await?.into_inner();

        let reactions = response
            .reactions
            .into_iter()
            .map(|r| ReactionItem {
                reaction_id: r.reaction_id,
                user_id: r.user_id,
                reaction_type: r.reaction_type,
                emotion_word: r.emotion_word,
                opinion_text: r.opinion_text,
                resonance_value: r.resonance_value,
                created_at: r.created_at,
            })
            .collect();

        Ok((reactions, response.total_count, response.has_more))
    }

    pub async fn get_reaction_distribution(
        &mut self,
        anchor_id: &str,
    ) -> Result<ReactionDistribution, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::GetReactionDistributionRequest {
            anchor_id: anchor_id.to_string(),
        });

        let response = self.inner.get_reaction_distribution(request).await?.into_inner();

        if response.found {
            let dist = response.distribution
                .ok_or_else(|| ApiError::Internal("共鸣引擎返回空分布数据".into()))?;
            Ok(ReactionDistribution {
                resonance_count: dist.resonance_count,
                neutral_count: dist.neutral_count,
                opposition_count: dist.opposition_count,
                unexperienced_count: dist.unexperienced_count,
                harmful_count: dist.harmful_count,
                total_count: dist.total_count,
            })
        } else {
            Ok(ReactionDistribution {
                resonance_count: 0,
                neutral_count: 0,
                opposition_count: 0,
                unexperienced_count: 0,
                harmful_count: 0,
                total_count: 0,
            })
        }
    }

    pub async fn get_relationship_score(
        &mut self,
        user_a: &str,
        user_b: &str,
    ) -> Result<RelationshipScore, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::GetRelationshipScoreRequest {
            user_a_id: user_a.to_string(),
            user_b_id: user_b.to_string(),
        });

        let response = self.inner.get_relationship_score(request).await?.into_inner();

        Ok(RelationshipScore {
            found: response.found,
            score_a_to_b: response.score_a_to_b,
            score_b_to_a: response.score_b_to_a,
            topic_diversity: response.topic_diversity,
            resonance_count: response.resonance_count,
        })
    }

    pub async fn find_resonance_pairs(
        &mut self,
        user_id: &str,
    ) -> Result<Vec<ResonancePair>, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::FindResonancePairsRequest {
            user_id: user_id.to_string(),
        });

        let response = self.inner.find_resonance_pairs(request).await?.into_inner();

        let pairs = response
            .pairs
            .into_iter()
            .map(|p| ResonancePair {
                other_user_id: p.other_user_id,
                relationship_score: p.relationship_score,
                shared_anchors: p.shared_anchors,
            })
            .collect();

        Ok(pairs)
    }

    pub async fn encode_text(
        &mut self,
        texts: Vec<String>,
    ) -> Result<EncodeTextResponse, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::EncodeTextRequest { texts });

        let response = self.inner.encode_text(request).await?.into_inner();

        Ok(EncodeTextResponse {
            vectors: response.vectors,
            dimension: response.dimension,
        })
    }
}
