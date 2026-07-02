from google.protobuf import message
m = message.Message
methods = [x for x in dir(m) if 'FromString' in x or 'Parse' in x or 'Merge' in x]
print("Deserialization methods:", methods)

# Check if FromString exists as a class method
print("FromString is class method:", hasattr(m, 'FromString'))

# Try to create a simple message and check
from google.protobuf import descriptor_pb2
print("descriptor_pb2 methods:", [x for x in dir(descriptor_pb2.FileDescriptorProto) if 'FromString' in x or 'Parse' in x or 'Merge' in x])
