import socket
import json

def test_endpoint():
    # Register first
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 8080))
    
    body = json.dumps({"device_fingerprint": "test123"})
    req = f"POST /api/v1/auth/register HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nX-Device-Id: test-dev\r\nContent-Length: {len(body)}\r\n\r\n{body}"
    s.send(req.encode())
    resp = s.recv(4096).decode()
    s.close()
    
    # Extract token
    lines = resp.split("\r\n")
    body_start = resp.find("\r\n\r\n") + 4
    resp_body = resp[body_start:]
    data = json.loads(resp_body)
    token = data["data"]["token"]
    
    # Test anchor detail
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.connect(("localhost", 8080))
    req2 = f"GET /api/v1/anchors/a_seed_001 HTTP/1.1\r\nHost: localhost\r\nAuthorization: Bearer {token}\r\nX-Device-Id: test-dev\r\n\r\n"
    s2.send(req2.encode())
    resp2 = s2.recv(4096).decode()
    s2.close()
    
    print("Response:", resp2[:500])

test_endpoint()
