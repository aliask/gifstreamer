#!/usr/bin/env python3

import struct
from PIL import Image


class FramePDU:
    IDENT = 0x1234
    height = 0
    width = 0
    pixeldata = b""

    def __init__(self, height: int, width: int, pixeldata: bytes):
        self.height = height
        self.width = width
        self.pixeldata = pixeldata

    @classmethod
    def from_image(cls, image):
        if type(image) is str:
            img = Image.open(image).convert("RGB")
        elif type(image) is Image.Image:
            img = image.convert("RGB")
        else:
            raise ValueError(f"Unsupported type: {type(image)}")

        img.load()
        pixeldata = b""
        for y in range(img.height):
            for x in range(img.width):
                (r, g, b) = img.getpixel((x, img.height - y - 1))
                a = 255
                pixeldata += struct.pack("BBBB", r, g, b, a)
        return cls(height=img.height, width=img.width, pixeldata=pixeldata)

    def as_binary(self):
        header = struct.pack(
            "HHHH", self.IDENT, self.height, self.width, len(self.pixeldata)
        )
        return header + self.pixeldata


class CommandPDU:
    IDENT = 0x4321
    CMD_BRIGHTNESS = 0
    CMD_PRIORITY = 1

    def __init__(self, command, value):
        self.command = command
        self.value = value

    def as_binary(self):
        return struct.pack("HBB", self.IDENT, self.command, self.value)
