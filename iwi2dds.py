import io
import struct
import sys


def iwi2dds(iwi, dds):

    dds_flags = {
        "DDSD_CAPS": 0x1,
        "DDSD_HEIGHT": 0x2,
        "DDSD_WIDTH": 0x4,
        "DDSD_PITCH": 0x8,
        "DDSD_PIXELFORMAT": 0x1000,
        "DDSD_MIPMAPCOUNT": 0x20000,
        "DDSD_LINEARSIZE": 0x80000,
        "DDSD_DEPTH": 0x800000
    }

    dds_pixelformat_flags = {
        "DDPF_ALPHAPIXELS": 0x1,
        "DDPF_ALPHA": 0x2,
        "DDPF_FOURCC": 0x4,
        "DDPF_RGB": 0x40,
        "DDPF_YUV": 0x200,
        "DDPF_LUMINANCE": 0x20000
    }

    dds_caps_flags = {
        "DDSCAPS_COMPLEX": 0x8,
        "DDSCAPS_MIPMAP": 0x400000,
        "DDSCAPS_TEXTURE": 0x1000
    }

    supported_image_formats = [0x1, 0x2, 0x3, 0x4, 0xB, 0xC, 0xD]

    dxtn_formats = {
        0xB: b"DXT1",
        0xC: b"DXT3",
        0xD: b"DXT5"
    }

    with open(iwi, "rb") as f:
        # A sincere thanks to Scobalula for his groundwork
        # struct IWIHeader
        # {
        #     uint8_t Magic[3];
        #     uint8_t Version;
        # };

        IWIHeader = struct.unpack("cccc", f.read(4))
        if IWIHeader[3] not in (b"\x06", b"\x08"):
            raise Exception("Unsupported IWI version.")

        if IWIHeader[3] == b"\x08":
            f.seek(0x8)

        # struct IWIInfo
        # {
        #     uint8_t ImageFormat;
        #     uint8_t ImageFlags;
        #     uint16_t ImageWidth;
        #     uint16_t ImageHeight;
        # };

        IWIInfo = struct.unpack("BBHH", f.read(6))

        if IWIInfo[0] not in supported_image_formats:
            raise Exception("Unsupported image format {}.".format(IWIInfo[0]))

        if IWIHeader[3] == b"\x06":
            f.seek(0xC)
        if IWIHeader[3] == b"\x08":
            f.seek(0x10)

        # struct IWISmallMips
        # {
        #     int32_t MipOffset1;
        #     int32_t MipOffset2;
        #     int32_t MipOffset3;
        #     int32_t MipOffset4;
        # };

        mips = struct.unpack("iiii", f.read(16))
        hasMips = False
        if mips[0] == mips[1] or mips[0] == mips[3]:
            offsetToDump = f.tell()
        else:
            offsetToDump = mips[1]
            hasMips = True

        f.seek(0, io.SEEK_END)
        sizeToDump = f.tell() - offsetToDump

        f.seek(offsetToDump)
        dds_data = f.read(sizeToDump)
        if hasMips:
            f.seek(mips[2])
            dds_data += f.read(mips[1] - mips[2])
            f.seek(mips[3])
            dds_data += f.read(mips[2] - mips[3])

    with open(dds, "wb") as f:
        # Ref https://docs.microsoft.com/en-us/windows/win32/direct3ddds/dds-header

        if IWIInfo[0] == 0x1: # ARGB8
            dds_pixelformat_header = \
                struct.pack("I"*8,
                    32, # DDS_PIXELFORMAT_dwSize
                    dds_pixelformat_flags["DDPF_RGB"] | dds_pixelformat_flags["DDPF_ALPHAPIXELS"], # DDS_PIXELFORMAT_dwFlags
                    0x0, # DDS_PIXELFORMAT_dwFourCC
                    32, # DDS_PIXELFORMAT_dwRGBBitCount
                    0x00ff0000, # DDS_PIXELFORMAT_dwRBitMask
                    0x0000ff00, # DDS_PIXELFORMAT_dwGBitMask
                    0x000000ff, # DDS_PIXELFORMAT_dwBBitMask
                    0xff000000 # DDS_PIXELFORMAT_dwABitMask
                )
        elif IWIInfo[0] == 0x2: # RGB8
            dds_pixelformat_header = \
                struct.pack("I"*8,
                    32, # DDS_PIXELFORMAT_dwSize
                    dds_pixelformat_flags["DDPF_RGB"], # DDS_PIXELFORMAT_dwFlags
                    0x0,  # DDS_PIXELFORMAT_dwFourCC
                    24,  # DDS_PIXELFORMAT_dwRGBBitCount
                    0xff0000,  # DDS_PIXELFORMAT_dwRBitMask
                    0x00ff00,  # DDS_PIXELFORMAT_dwGBitMask
                    0x0000ff,  # DDS_PIXELFORMAT_dwBBitMask
                    0x0  # DDS_PIXELFORMAT_dwABitMask
                )
        elif IWIInfo[0] == 0x3: # ARGB4
            dds_pixelformat_header = \
                struct.pack("I"*8,
                    32,  # DDS_PIXELFORMAT_dwSize
                    dds_pixelformat_flags["DDPF_RGB"],  # DDS_PIXELFORMAT_dwFlags
                    0x0,  # DDS_PIXELFORMAT_dwFourCC
                    16,  # DDS_PIXELFORMAT_dwRGBBitCount
                    0b00001111_00000000,  # DDS_PIXELFORMAT_dwRBitMask
                    0b00000000_11110000,  # DDS_PIXELFORMAT_dwGBitMask
                    0b00000000_00001111,  # DDS_PIXELFORMAT_dwBBitMask
                    0b11110000_00000000  # DDS_PIXELFORMAT_dwABitMask
                )
        elif IWIInfo[0] == 0x4: # A8
            dds_pixelformat_header = \
                struct.pack("I"*8,
                    32,  # DDS_PIXELFORMAT_dwSize
                    dds_pixelformat_flags["DDPF_ALPHA"],  # DDS_PIXELFORMAT_dwFlags
                    0x0,  # DDS_PIXELFORMAT_dwFourCC
                    8,  # DDS_PIXELFORMAT_dwRGBBitCount
                    0x0,  # DDS_PIXELFORMAT_dwRBitMask
                    0x0,  # DDS_PIXELFORMAT_dwGBitMask
                    0x0,  # DDS_PIXELFORMAT_dwBBitMask
                    0xff  # DDS_PIXELFORMAT_dwABitMask
                )
        elif IWIInfo[0] in dxtn_formats.keys(): # DXTn
            dds_pixelformat_header =  struct.pack("II", 32, dds_pixelformat_flags["DDPF_FOURCC"]) + \
                                      dxtn_formats[IWIInfo[0]] + \
                                      struct.pack("IIIII", 0x0, 0x0, 0x0, 0x0, 0x0)

        capsFlags = dds_caps_flags["DDSCAPS_TEXTURE"] | \
                    dds_caps_flags["DDSCAPS_MIPMAP"] | \
                    dds_caps_flags["DDSCAPS_COMPLEX"] if hasMips else dds_caps_flags["DDSCAPS_TEXTURE"]

        f.write(b"DDS ")
        f.write(struct.pack("I", 124)) # dwSize
        f.write(struct.pack("I", dds_flags["DDSD_CAPS"] |
                            dds_flags["DDSD_HEIGHT"] |
                            dds_flags["DDSD_WIDTH"] |
                            dds_flags["DDSD_PIXELFORMAT"] |
                            dds_flags["DDSD_LINEARSIZE"] |
                            dds_flags["DDSD_MIPMAPCOUNT"]
                )
        ) # dwFlags

        f.write(struct.pack("I", IWIInfo[3])) # dwHeight
        f.write(struct.pack("I", IWIInfo[2])) # dwWidth
        f.write(struct.pack("I", len(dds_data))) # dwPitchOrLinearSize
        f.write(struct.pack("I", 0x0)) # dwDepth
        f.write(struct.pack("I", 0x3 if hasMips else 0x0)) # dwMipMapCount
        for _ in range(0, 11):
            f.write(struct.pack("I", 0x0)) # dwReserved1[11]
        f.write(dds_pixelformat_header) # dds-pixelformat struct
        f.write(struct.pack("I", capsFlags)) # dwCaps
        f.write(struct.pack("I", 0x0)) # dwCaps2
        f.write(struct.pack("I", 0x0)) # dwCaps3
        f.write(struct.pack("I", 0x0)) # dwCaps4
        f.write(struct.pack("I", 0x0)) # dwReserved2
        f.write(dds_data)


if __name__ == "__main__":
    iwi2dds(sys.argv[1], sys.argv[2])
