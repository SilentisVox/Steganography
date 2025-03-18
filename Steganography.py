import argparse
import zlib

class Steganography:

    ## -------------------------------- #### -------------------------------- #### -------------------------------- ##

    def __init__(self, file_name: str, file: bytes) -> None:
        self.FILE_NAME                  = file_name
        self.RAW_FILE                   = file
        
        self.RESOLUTION                 = (None, None)
        self.COMPRESSED_DATA            = b""
        self.DECOMPRESS_DATA            = b""
        self.PIXEL_DATA                 = []

    ## -------------------------------- #### -------------------------------- #### -------------------------------- ##

    # Simple tools we need are to quickly convert
    # a byte to bits, and bits to a byte.

    def byte_to_bits(self, byte: bytes) -> list:
        binary                          = format(byte, "08b")
        bits                            = []

        for bit in binary:
            bits.append(int(bit))

        return bits

    def bits_to_byte(self, bits: list) -> bytes:
        byte_list                       = []

        for index, bit in enumerate(bits):
            bit_operation               = bit << (7 - index)
            byte_list.append(bit_operation)

        byte                            = sum(byte_list)

        return byte

    ## -------------------------------- #### -------------------------------- #### -------------------------------- ##

    # Quickly verify our file's authenticity, and
    # find our image resolution

    def verify_png(self) -> None:
        valid_header                    = b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"
        file_header                     = self.RAW_FILE[:8]

        if file_header != file_header:
            print("[!] Invalid File Type.")
            return False

        return True

    def find_resolution(self) -> None:
        bytes_width                     = self.RAW_FILE[16:20]
        bytes_height                    = self.RAW_FILE[20:24]

        pixel_width                     = int.from_bytes(bytes_width, byteorder="big")
        pixel_height                    = int.from_bytes(bytes_height, byteorder="big")

        print("    ╰─ Resolution: {} x {}".format(pixel_width, pixel_height))

        self.RESOLUTION                 = (pixel_width, pixel_height)

    ## -------------------------------- #### -------------------------------- #### -------------------------------- ##

    # After we retrieve the decompressed content,
    # each row of pixels may have an algorithm
    # applied to it to help further reduce file
    # size.

    # There are 4 possible algorithms applied to
    # a given row, denoted by the first byte of
    # each row.

    def pixel_sub(self, pixel_row: bytearray, pixel_row_length: int, pixel_row_previous: bytearray) -> bytearray:
       for index in range(4, pixel_row_length):
            pixel_row[index]            = (pixel_row[index] + pixel_row[index - 4]) % 256

       return pixel_row

    def pixel_up(self, pixel_row: bytearray, pixel_row_length: int, pixel_row_previous: bytearray) -> bytearray:
        for index in range(pixel_row_length):
            pixel_row[index]            = (pixel_row[index] + pixel_row_previous[index]) % 256

        return pixel_row

    def pixel_average(self, pixel_row: bytearray, pixel_row_length: int, pixel_row_previous: bytearray) -> bytearray:
        for index in range(pixel_row_length):
            pixel_left                  = pixel_row[index - 4] if index >= 4 else 0
            pixel_above                 = pixel_row_previous[index]
            pixel_row[index]            = (pixel_row[index] + ((pixel_left + pixel_above) // 2)) % 256

        return pixel_row

    def pixel_paeth(self, pixel_row: bytearray, pixel_row_length: int, pixel_row_previous: bytearray) -> bytearray:

        def paeth_predictor(a, b, c):
            p                           = a + b - c
            pa                          = abs(p - a)
            pb                          = abs(p - b)
            pc                          = abs(p - c)

            if pa <= pb and pa <= pc:
                return a
            elif pb <= pc:
                return b
            else:
                return c

        for index in range(pixel_row_length):
            pixel_left                  = pixel_row[index - 4] if index >= 4 else 0
            pixel_above                 = pixel_row_previous[index]
            pixel_left_above            = pixel_row_previous[index - 4] if index >= 4 else 0
            pixel_paeth                 = paeth_predictor(pixel_left, pixel_above, pixel_left_above)
            pixel_row[index]            = (pixel_row[index] + pixel_paeth) % 256

        return pixel_row

    def process_pixel_row(self, pixel_row: bytearray, pixel_row_previous: bytearray) -> bytearray:
        pixel_row_start                 = pixel_row[0]
        pixel_row                       = pixel_row[1:]
        pixel_row_length                = len(pixel_row)

        if pixel_row_start == 0:
            return pixel_row

        pixel_process                   = {
            1 : self.pixel_sub,
            2 : self.pixel_up,
            3 : self.pixel_average,
            4 : self.pixel_paeth
        }

        pixel_row                       = pixel_process[pixel_row_start](pixel_row, pixel_row_length, pixel_row_previous)

        return pixel_row

    # PNGs can have multiple compressed data
    # sections for efficiency, so we must parse
    # our data to grab all sections.

    def seek_idats(self, position: int) -> int:
        idat_position                   = self.RAW_FILE.find(b"IDAT", position)

        if idat_position == -1:
            return False

        content_length                  = self.RAW_FILE[idat_position - 4:idat_position]
        content_length                  = int.from_bytes(content_length, byteorder="big")
        content_position                = idat_position + 4
        content                         = self.RAW_FILE[content_position:content_position + content_length]

        self.COMPRESSED_DATA           += content

        last_position                   = content_position + content_length + 4

        return last_position

    # Once we have all of our compressed datas,
    # we can decompress it, and find all RBG data
    # in a bit-like format. 

    # This is important because we either want to
    # retrieve or ipmlant data based on the bytes
    # in bit format.

    def find_pixel_data(self) -> None:
        idat_section_position           = 0

        while True:
            idat_section_position       = self.seek_idats(idat_section_position)

            if not idat_section_position:
                break

        pixel_deflate_data              = self.COMPRESSED_DATA[2:]

        print("    ╰─ Decompressing Image Data.")

        pixel_data                      = zlib.decompress(pixel_deflate_data, -15)

        self.DECOMPRESS_DATA            = pixel_data
        
        pixel_rows                      = []

        pixel_data_length               = len(pixel_data)
        pixel_row_length                = self.RESOLUTION[0] * 4 + 1
        
        pixel_row_previous              = bytearray()

        print("    ╰─ Analyzing Image Data.\n")

        for index in range(0, pixel_data_length, pixel_row_length):
            pixel_row                   = pixel_data[index:index + pixel_row_length]
            pixel_row                   = bytearray(pixel_row)
            pixel_row_manipulated       = self.process_pixel_row(pixel_row, pixel_row_previous)
            pixel_rows.append(pixel_row_manipulated)
            pixel_row_previous          = pixel_row_manipulated

        rgb_bits_rows                   = []

        for pixel_row in pixel_rows:
            pixel_row_length            = self.RESOLUTION[0] * 4

            for index in range(0, pixel_row_length, 4):
                rgb                     = pixel_row[index:index + 3]
                
                for byte in rgb:
                    bits                = self.byte_to_bits(byte)
                    rgb_bits_rows      += bits

        self.PIXEL_DATA                 = rgb_bits_rows

    ## -------------------------------- #### -------------------------------- #### -------------------------------- ##

    # The data extracted will be the last bit in
    # every byte. We can contain all the bits to
    # one list. Now manually extract every 8 bits
    # and convert it to a byte.

    def extract_hidden_data(self) -> None:
        least_significant_bits          = []

        pixel_data_length               = len(self.PIXEL_DATA)

        for index in range(0, pixel_data_length, 8):
            bit                         = self.PIXEL_DATA[index + 7]
            least_significant_bits.append(bit)

        lsb_length                      = len(least_significant_bits)

        all_bytes                       = bytearray()

        for index in range(0, lsb_length, 8):
            all_byte_in_bits            = least_significant_bits[index:index + 8]
            all_byte                    = self.bits_to_byte(all_byte_in_bits)
            all_bytes.append(all_byte)

        all_data                        = bytes(all_bytes)
        hidden_data_length              = all_data[:3]
        hidden_data_length              = int.from_bytes(hidden_data_length, byteorder="big")

        hidden_data                     = all_data[3:hidden_data_length + 3]

        return hidden_data

    ## -------------------------------- #### -------------------------------- #### -------------------------------- ##

    # We want to turn our data into a bit array.
    # Then we will take every bit, and replace
    # the LSB (least significant bit) with our
    # bit.

    def implant_hidden_data(self, data: bytes) -> None:
        data_length                     = len(data).to_bytes(3, byteorder="big")
        data                            = data_length + data
        data_bits                       = []

        print("    ╰─ Implanting Data.")

        for byte in data:
            bits                        = self.byte_to_bits(byte)
            data_bits                  += bits

        for index, bit in enumerate(data_bits):
            self.PIXEL_DATA[index * 8 + 7] = bit

    ## -------------------------------- #### -------------------------------- #### -------------------------------- ##

    def calculate_crc(self, chunk_type: bytes, chunk_data: bytes) -> bytes:
        crc_hash                        = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        crc_hash_bytes                  = crc_hash.to_bytes(4, byteorder="big")

        return crc_hash_bytes

    def create_new_image(self) -> bytes:
        print("    ╰─ Formatting PNG.")

        pixel_data_length               = len(self.PIXEL_DATA)
        rgba_bytes                      = bytearray()

        for alpha_index, rgb_index in enumerate(range(0, pixel_data_length, 8)):
            byte_in_bits                = self.PIXEL_DATA[rgb_index:rgb_index + 8]
            byte                        = self.bits_to_byte(byte_in_bits)
            rgba_bytes.append(byte)

            if (alpha_index + 1) % 3 == 0:
                rgba_bytes.append(0xff)

        rgba_bytes_length               = len(rgba_bytes)
        pixel_row_length                = self.RESOLUTION[0] * 4

        pixel_data                      = b""

        print("    ╰─ Adding Row Bytes.")

        for row_index, pixel_index in enumerate(range(0, rgba_bytes_length, pixel_row_length)):
            pixel_row                   = rgba_bytes[pixel_index:pixel_index + pixel_row_length]
            pixel_row                   = b"\x00" + pixel_row
            pixel_data                 += pixel_row

        # Create PNG compressed data.

        print("    ╰─ Compressing Image Data.")

        zlib_header                     = b"\x78\xDA"
        compressed_data                 = zlib.compress(pixel_data, level=8)
        deflate_data                    = compressed_data[2:]

        idat_data                       = zlib_header + deflate_data

        # PNG

        png_checksum                    = b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"

        # IHDR

        ihdr                            = b"\x49\x48\x44\x52"
        data_length                     = b"\x00\x00\x00\x0d"

        width                           = self.RESOLUTION[0].to_bytes(4, byteorder="big")
        height                          = self.RESOLUTION[1].to_bytes(4, byteorder="big")
        tail_data                       = b"\x08\x06\x00\x00\x00"

        ihdr_data                       = (
            width   +
            height  +
            tail_data
        )

        crc                             = self.calculate_crc(ihdr, ihdr_data)
        ihdr_chunk                      = data_length + ihdr + ihdr_data + crc

        # IDAT

        idat                            = b"\x49\x44\x41\x54"
        data_length                     = len(bytearray(idat_data)).to_bytes(4, byteorder="big")
        crc                             = self.calculate_crc(idat, idat_data)

        idat_chunk                      = data_length + idat + idat_data + crc

        # IEND

        data_length                     = b"\x00\x00\x00\x00"
        iend                            = b"\x49\x45\x4e\x44"
        crc                             = b"\xae\x42\x60\x82"

        iend_chunk                      = data_length + iend + crc

        # FULL PNG

        png                             = png_checksum + ihdr_chunk + idat_chunk + iend_chunk

        return png

def extract_data(steganography: Steganography, out_file: str) -> bool:
    print("[+] Extracting Hidden Data.")

    hidden_data                         = steganography.extract_hidden_data()
    
    if not out_file:
        print("\n", hidden_data, "\n")
        return

    file                        = open(out_file, "wb")
    file.write(hidden_data)
    file.close()

def implant_data(steganography: Steganography, in_file: str, out_file: str) -> bool:
    print("[+] Implanting Hidden Data.")

    data                                = open(in_file, "rb").read()
    steganography.implant_hidden_data(data)

    new_png                             = steganography.create_new_image()

    with open(out_file, "wb") as file:
        file.write(new_png)

def test_steganography():
    print("[i] [STEGANOGRAPHY] Press <Enter> To Run ...", end="")
    input()

    parse                               = argparse.ArgumentParser(description="Steganography Tool")
    group                               = parse.add_mutually_exclusive_group(required=True)

    parse.add_argument("input_file", type=str,            help="The image file to read from")

    group.add_argument("--implant",  action="store_true", help="Implant data into the image")
    group.add_argument("--extract",  action="store_true", help="Extract data from the image")

    parse.add_argument("--in-file",  type=str,            help="File to implant into the image (Required for --implant)")
    parse.add_argument("--out-file", type=str,            help="Output file (Required for --implant, Optional for --extract)")
    
    args                                = parse.parse_args()

    if args.implant and (not args.in_file or not args.out_file):
        parse.error("--implant requires both --in-file and --out-file.")

    file_name                           = args.input_file
    png                                 = open(file_name, "rb").read()

    steganography                       = Steganography(file_name, png)
    RESULT                              = steganography.verify_png()

    if not RESULT:
        return

    steganography.find_resolution()
    steganography.find_pixel_data()

    in_file                             = args.in_file  if args.in_file  else ""
    out_file                            = args.out_file if args.out_file else ""

    if args.extract:
        RESULT                          = extract_data(steganography, out_file)

    if args.implant:
        RESULT                          = implant_data(steganography, in_file, out_file)

    print("[#] [STEGANOGRAPHY] Press <Enter> To Quit ...")
    input()

if __name__ == "__main__":
    test_steganography()