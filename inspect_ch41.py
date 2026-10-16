import re

with open(r'd:\Singvox\Singvox\avatar\models\Ch41_nonPBR.fbx', 'rb') as f:
    data = f.read()
    
strings = re.findall(b'[a-zA-Z0-9_:]{4,}', data)
strings = [s.decode('ascii', errors='ignore') for s in strings]
bones = set([s for s in strings if 'mixamorig' in s.lower()])

print("Bones in Ch41:")
for b in sorted(list(bones)):
    print(b)
