//! 配置单元测试

use standby_gateway::config::GatewayConfig;

#[test]
fn test_config_structure() {
    // 测试配置结构体的基本属性
    let config = GatewayConfig {
        port: 8080,
        jwt_secret: "test-secret".to_string(),
        jwt_expiry_hours: 24,
        device_secret: "device-secret".to_string(),
        engine_anchor_url: "http://localhost:8090".to_string(),
        engine_resonance_url: "http://localhost:8091".to_string(),
        engine_governance_url: "http://localhost:8092".to_string(),
        engine_context_url: "http://localhost:8094".to_string(),
        rate_limit_per_minute: 60,
        log_level: "info".to_string(),
        request_timeout_secs: 30,
    };

    assert_eq!(config.port, 8080);
    assert_eq!(config.jwt_secret, "test-secret");
    assert_eq!(config.jwt_expiry_hours, 24);
    assert_eq!(config.rate_limit_per_minute, 60);
}

#[test]
fn test_config_clone() {
    let config = GatewayConfig {
        port: 8080,
        jwt_secret: "test-secret".to_string(),
        jwt_expiry_hours: 24,
        device_secret: "device-secret".to_string(),
        engine_anchor_url: "http://localhost:8090".to_string(),
        engine_resonance_url: "http://localhost:8091".to_string(),
        engine_governance_url: "http://localhost:8092".to_string(),
        engine_context_url: "http://localhost:8094".to_string(),
        rate_limit_per_minute: 60,
        log_level: "info".to_string(),
        request_timeout_secs: 30,
    };

    let cloned = config.clone();

    assert_eq!(config.port, cloned.port);
    assert_eq!(config.jwt_secret, cloned.jwt_secret);
    assert_eq!(config.jwt_expiry_hours, cloned.jwt_expiry_hours);
    assert_eq!(config.rate_limit_per_minute, cloned.rate_limit_per_minute);
}

#[test]
fn test_config_debug_format() {
    let config = GatewayConfig {
        port: 8080,
        jwt_secret: "test-secret".to_string(),
        jwt_expiry_hours: 24,
        device_secret: "device-secret".to_string(),
        engine_anchor_url: "http://localhost:8090".to_string(),
        engine_resonance_url: "http://localhost:8091".to_string(),
        engine_governance_url: "http://localhost:8092".to_string(),
        engine_context_url: "http://localhost:8094".to_string(),
        rate_limit_per_minute: 60,
        log_level: "info".to_string(),
        request_timeout_secs: 30,
    };

    let debug_str = format!("{:?}", config);

    assert!(debug_str.contains("port"));
    assert!(debug_str.contains("jwt_secret"));
    assert!(debug_str.contains("jwt_expiry_hours"));
    assert!(debug_str.contains("rate_limit_per_minute"));
    assert!(debug_str.contains("engine_anchor_url"));
}

#[test]
fn test_config_default_values() {
    // 测试默认值是否符合预期
    let config = GatewayConfig {
        port: 8080,
        jwt_secret: "test".to_string(),
        jwt_expiry_hours: 24,
        device_secret: "test".to_string(),
        engine_anchor_url: "http://localhost:8090".to_string(),
        engine_resonance_url: "http://localhost:8091".to_string(),
        engine_governance_url: "http://localhost:8092".to_string(),
        engine_context_url: "http://localhost:8094".to_string(),
        rate_limit_per_minute: 60,
        log_level: "info".to_string(),
        request_timeout_secs: 30,
    };

    // 验证默认端口
    assert_eq!(config.port, 8080);

    // 验证默认过期时间
    assert_eq!(config.jwt_expiry_hours, 24);

    // 验证默认速率限制
    assert_eq!(config.rate_limit_per_minute, 60);

    // 验证默认日志级别
    assert_eq!(config.log_level, "info");

    // 验证默认超时时间
    assert_eq!(config.request_timeout_secs, 30);
}
