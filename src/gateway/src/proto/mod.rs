//! Protobuf 生成的 gRPC 客户端代码
//!
//! 由 build.rs 从 src/proto/engines.proto 自动生成

pub mod common {
    tonic::include_proto!("standby.common");
}

pub mod engines {
    tonic::include_proto!("standby.engines");
}
