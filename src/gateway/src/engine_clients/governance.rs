use tonic::transport::Channel;

use crate::error::ApiError;
use crate::proto::engines::governance_engine_client::GovernanceEngineClient;
use crate::proto::common::{GovernanceLevel, ReactionSummary};
use crate::proto::engines::MarkerCreditInfo;
use crate::models::governance::*;

pub struct GovernanceClient {
    inner: GovernanceEngineClient<Channel>,
}

impl Clone for GovernanceClient {
    fn clone(&self) -> Self {
        Self {
            inner: self.inner.clone(),
        }
    }
}

impl GovernanceClient {
    pub async fn new(url: &str) -> anyhow::Result<Self> {
        let inner = GovernanceEngineClient::connect(url.to_string()).await?;
        Ok(Self { inner })
    }

    pub async fn check_health(&self) -> bool {
        let mut inner = self.inner.clone();
        let req = tonic::Request::new(super::super::proto::engines::CheckMarkCredibilityRequest {
            marker_token_hash: String::new(),
        });
        inner.check_mark_credibility(req).await.is_ok()
    }

    pub async fn evaluate_content(
        &mut self,
        req: EvaluateContentRequest,
    ) -> Result<GovernanceDecision, ApiError> {
        let marker_credits = req
            .marker_credits
            .unwrap_or_default()
            .into_iter()
            .map(|m| MarkerCreditInfo {
                marker_token_hash: m.marker_token_hash,
                credit_score: m.credit_score,
                total_marks: m.total_marks,
            })
            .collect();

        let total = req.resonance_count
            + req.neutral_count
            + req.opposition_count
            + req.unexperienced_count
            + req.harmful_count;

        let request = tonic::Request::new(super::super::proto::engines::EvaluateContentRequest {
            content_id: req.content_id.clone(),
            content_type: req.content_type.unwrap_or_else(|| "anchor".into()),
            reaction_summary: Some(ReactionSummary {
                resonance_count: req.resonance_count,
                neutral_count: req.neutral_count,
                opposition_count: req.opposition_count,
                unexperienced_count: req.unexperienced_count,
                harmful_count: req.harmful_count,
                total_count: total,
            }),
            marker_credits,
        });

        let response = self.inner.evaluate_content(request).await?.into_inner();
        let decision = response.decision
            .ok_or_else(|| ApiError::Internal("治理引擎返回空决策".into()))?;

        let level_str = match decision.level() {
            GovernanceLevel::L0Normal => "L0_正常",
            GovernanceLevel::L1Observe => "L1_观察",
            GovernanceLevel::L2Demoted => "L2_降权",
            GovernanceLevel::L3Suspended => "L3_暂停",
            GovernanceLevel::L4Removed => "L4_移除",
            GovernanceLevel::Disputed => "争议",
            _ => "L0_正常",
        };

        Ok(GovernanceDecision {
            content_id: decision.content_id,
            level: level_str.to_string(),
            harmful_weight: decision.harmful_weight,
            marker_avg_credit: decision.marker_avg_credit,
            reason: decision.reason,
            actions: decision.actions,
        })
    }

    pub async fn detect_anomaly(
        &mut self,
        req: DetectAnomalyRequest,
    ) -> Result<Vec<AnomalyReport>, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::DetectAnomalyRequest {
            anchor_id: req.anchor_id,
            mark_timestamps: req.mark_timestamps.unwrap_or_default(),
            marker_ids: req.marker_ids.unwrap_or_default(),
            reactions_by_type: req.reactions_by_type.unwrap_or_default(),
        });

        let response = self.inner.detect_anomaly(request).await?.into_inner();

        let anomalies = response
            .anomalies
            .into_iter()
            .map(|a| AnomalyReport {
                anomaly_type: a.anomaly_type,
                description: a.description,
                severity: a.severity,
                actions: a.actions,
            })
            .collect();

        Ok(anomalies)
    }

    pub async fn check_credibility(
        &mut self,
        marker_hash: &str,
    ) -> Result<MarkerCredibility, ApiError> {
        let request = tonic::Request::new(super::super::proto::engines::CheckMarkCredibilityRequest {
            marker_token_hash: marker_hash.to_string(),
        });

        let response = self.inner.check_mark_credibility(request).await?.into_inner();

        Ok(MarkerCredibility {
            credit_score: response.credit_score,
            total_marks: response.total_marks,
            accuracy_rate: response.accuracy_rate,
            is_suspicious: response.is_suspicious,
        })
    }
}
