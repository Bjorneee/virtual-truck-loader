import hashlib

def color_from_id(box_id: str):
    digest = hashlib.md5(box_id.encode("utf-8")).digest()
    r = 0.35 + (digest[0] / 255.0) * 0.55
    g = 0.35 + (digest[1] / 255.0) * 0.55
    b = 0.35 + (digest[2] / 255.0) * 0.55
    return (r, g, b, 1.0)