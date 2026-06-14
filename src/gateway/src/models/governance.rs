use serde::{Deserialize, Serialize};

/// 治理级别枚举 (与 Proto GovernanceLevel 对齐)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum GovernanceLevel {
    #[serde(rename = "L0_NORMAL")]
    L0Normal,
    #[serde(rename = "L1_OBSERVE")]
    L1Observe,
    #[serde(rename = "L2_DEMOTED")]
    L2Demoted,
    #[serde(rename = "L3_SUSPENDED")]
    L3Suspended,
    #[serde(rename = "L4_REMOVED")]
    L4Removed,
    #[serde(rename = "DISPUTED")]
    Disputed,
}

impl GovernanceLevel {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::L0Normal => "L0_NORMAL",
            Self::L1Observe => "L1_OBSERVE",
            Self::L2Demoted => "L2_DEMOTED",
            Self::L3Suspended => "L3_SUSPENDED",
            Self::L4Removed => "L4_REMOVED",
            Self::Disputed => "DISPUTED",
        }
    }

    pub fn from_str(s: &str) -> Self {
        match s {
            "L0_NORMAL" => Self::L0Normal,
            "L1_OBSERVE" => Self::L1Observe,
            "L2_DEMOTED" => Self::L2Demoted,
            "L3_SUSPENDED" => Self::L3Suspended,
            "L4_REMOVED" => Self::L4Removed,
            "DISPUTED" => Self::Disputed,
            _ => Self::L0Normal,
        }
    }
}

/// 评估内容请求
#[derive(Debug, Deserialize)]
pub struct EvaluateContentRequest {
    pub content_id: String,
    pub content_type: Option<String>,
    pub resonance_count: i32,
    pub neutral_count: i32,
    pub opposition_count: i32,
    pub unexperienced_count: i32,
    pub harmful_count: i32,
    pub marker_credits: Option<Vec<MarkerCreditInput>>,
}

/// 标记者信用输入
#[derive(Debug, Deserialize)]
pub struct MarkerCreditInput {
    pub marker_token_hash: String,
    pub credit_score: f32,
    pub total_marks: i32,
}

/// 治理决策
#[derive(Debug, Serialize)]
pub struct GovernanceDecision {
    pub content_id: String,
    pub level: GovernanceLevel,
    pub harmful_weight: f32,
    pub marker_avg_credit: f32,
    pub reason: String,
    pub actions: Vec<String>,
}

/// 异常检测请求
#[derive(Debug, Deserialize)]
pub struct DetectAnomalyRequest {
    pub anchor_id: String,
    pub mark_timestamps: Option<Vec<i64>>,
    pub marker_ids: Option<Vec<String>>,
    pub reactions_by_type: Option<std::collections::HashMap<String, i32>>,
}

/// 异常报告
#[derive(Debug, Serialize)]
pub struct AnomalyReport {
    pub anomaly_type: String,
    pub description: String,
    pub severity: f32,
    pub actions: Vec<String>,
}

/// 标记者可信度
#[derive(Debug, Serialize)]
pub struct MarkerCredibility {
    pub credit_score: f32,
    pub total_marks: i32,
    pub accuracy_rate: f32,
    pub is_suspicious: bool,
}
