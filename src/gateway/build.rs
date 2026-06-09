fn main() -> Result<(), Box<dyn std::error::Error>> {
    let proto_dir = "../../src/proto";

    tonic_build::configure()
        .build_server(false)
        .build_client(true)
        .compile_protos(
            &[
                format!("{}/common.proto", proto_dir),
                format!("{}/engines.proto", proto_dir),
            ],
            &[proto_dir],
        )?;

    Ok(())
}
