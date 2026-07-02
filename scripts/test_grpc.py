import sys
sys.path.insert(0, '/mnt/d/LocalRepository/standby/src/proto/generated/python')
import grpc
from engines import engines_pb2_grpc, engines_pb2

channel = grpc.insecure_channel('localhost:8090')
stub = engines_pb2_grpc.AnchorEngineStub(channel)

# Test GetAnchorMetadata
req = engines_pb2.GetAnchorMetadataRequest(anchor_id='a_4966b937')
try:
    resp = stub.GetAnchorMetadata(req, timeout=5)
    print(f"GetAnchorMetadata: found={resp.found}, anchor_id={resp.anchor_id}, text={resp.text[:30] if resp.text else ''}")
except grpc.RpcError as e:
    print(f"GetAnchorMetadata error: {e.code()}: {e.details()}")

channel.close()
