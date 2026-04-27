fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 从 src/gateway/ 到 src/proto/
    let proto_root = "../proto";
    
    tonic_build::configure()
        .build_server(false)  // 只生成客户端
        .build_client(true)
        .compile_protos(
            &[
                format!("{proto_root}/common/common.proto"),
                format!("{proto_root}/engines/engines.proto"),
            ],
            &[proto_root.to_string()],
        )?;
    
    println!("cargo:rerun-if-changed={proto_root}/common/common.proto");
    println!("cargo:rerun-if-changed={proto_root}/engines/engines.proto");
    
    Ok(())
}
