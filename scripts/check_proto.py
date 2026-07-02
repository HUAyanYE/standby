import sys
sys.path.insert(0, '/app/src/proto/generated/python')
from engines import engines_pb2
attrs = [a for a in dir(engines_pb2) if 'Anchor' in a or 'anchor' in a]
print("Anchor-related attrs:", attrs)
