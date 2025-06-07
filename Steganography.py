import argparse
import PIL.Image

class Steganography:
    def __init__(self, file_path: str) -> None:
        self.input_image_path           = file_path
        self.input_image_data           = None
        self.pillow_image_object        = None
        self.extracted_bits             = []
        self.extracted_bytes            = bytearray()
        self.implanted_bits             = []
        self.implanted_data             = None

    # The 3 tools we need to fall back on would be quickly modifying
    # the LSB of a byte, converting a byte to a binary array, and a
    # binary array to a byte.

    def set_lsb(self, byte: bytes, bit: bytes) -> bytes:
        operated_byte                   = (byte & ~1) | (bit & 1)

        return operated_byte

    def byte_to_bits(self, byte: bytes) -> list:
        bits                            = []

        for index in range(7, -1, -1):
            bit                         = (byte >> index) & 1
            bits.append(bit)

        return bits

    def bits_to_byte(self, bits: list[bytes]) -> bytes:
        byte                            = 0

        for bit in bits:
            byte                        = (byte << 1) | bit

        return byte

    # Method to open our image as a Pillow object.

    def load_input_image(self) -> bool:
        self.pillow_image_object        = PIL.Image.open(self.input_image_path)

        if not self.pillow_image_object:
            return False

        image_object                    = self.pillow_image_object.getdata()
        pixels                          = list(image_object)
        self.input_image_data           = pixels

        return True

    # Methods to extract the length of the data and the data itself.

    def extract_length(self) -> int:
        bits                            = []
        length_bytes                    = bytearray()

        for pixel in self.input_image_data[:8]:
            for value in pixel[:3]:
                bit                     = value & 1
                bits.append(bit)

        for index in range(0, 24, 8):
            pseudo_byte                 = bits[index:index + 8]
            byte                        = self.bits_to_byte(pseudo_byte)
            length_bytes.append(byte)

        length                          = int.from_bytes(length_bytes, byteorder='big')

        return length

    def extract(self) -> bool:
        total_bytes                     = self.extract_length()
        to_read                         = ((total_bytes * 8) + 2) // 3

        for pixel in self.input_image_data[8:to_read + 8]:
            for value in pixel[:3]:
                bit                     = value & 1
                self.extracted_bits.append(bit)

        data_length                     = len(self.extracted_bits)

        for index in range(0, data_length - 8, 8):
            psuedo_byte                 = self.extracted_bits[index:index + 8]
            byte                        = self.bits_to_byte(psuedo_byte)
            self.extracted_bytes.append(byte)

        return True

    # Methods to load the data we wish to implant on our loaded image,
    # converting the data to bits, then setting each value of each
    # pixel to our desired byte containing our LSB.

    def load_implant_data(self, implant_path: str) -> bool:
        with open(implant_path, "rb") as file_buffer:
            file_data                   = file_buffer.read()

        if not file_data:
            return False

        self.implanted_bytes            = file_data

        return True

    def get_implant_bits(self) -> bool:
        data_bits                       = []
        data_size                       = len(self.implanted_bytes).to_bytes(3, byteorder="big")
        
        for byte in data_size:
            bits                        = self.byte_to_bits(byte)
            data_bits                  += bits

        for byte in self.implanted_bytes:
            bits                        = self.byte_to_bits(byte)
            data_bits                  += bits

        self.implanted_bits             = data_bits

        return True
    
    def set_implant_bits(self) -> bool:
        data_copy                       = self.input_image_data
        max_bits                        = len(self.implanted_bits)
        bit_index                       = 0
        pixels                          = (len(self.implanted_bits) // 3) + 1
        pixel_length                    = len(data_copy[0])

        for index in range(pixels):
            if pixel_length == 4:
                r, g, b, a              = data_copy[index]
            else:
                r, g, b                 = data_copy[index]

            if bit_index < max_bits:
                r                       = self.set_lsb(r, self.implanted_bits[bit_index])
            
            bit_index                  += 1

            if bit_index < max_bits:
                g                       = self.set_lsb(g, self.implanted_bits[bit_index])
                
            bit_index                  += 1

            if bit_index < max_bits:
                b                       = self.set_lsb(b, self.implanted_bits[bit_index])
               
            bit_index                   += 1

            if pixel_length == 4:
                data_copy[index]         = (r, g, b, a)
            else:
                data_copy[index]         = (r, g, b)

        self.implanted_bytes             = data_copy

        return True

    # Method to save our Pillow object back to a file.

    def save_steg_image(self, output_path: str) -> bool:
        mode                            = self.pillow_image_object.mode
        size                            = self.pillow_image_object.size
        image                           = PIL.Image.new(mode, size)
        image.putdata(self.implanted_bytes)
        image.save(output_path)

def main():
    parse                               = argparse.ArgumentParser(description="Steganography Tool")

    parse.add_argument("--extract",  type=str, help="Extract data from the image")
    parse.add_argument("--implant",  type=str, help="Implant data into the image")
    parse.add_argument("--in-file",  type=str, help="File to implant into the image (Required for --implant)")
    parse.add_argument("--out-file", type=str, help="Output file (Required for --implant, Optional for --extract)")
    
    args                                = parse.parse_args()

    if not bool(args.extract) ^ bool(args.implant):
        parse.error("must have either --extract or --implant")
        return

    if args.implant and not (args.in_file and args.out_file):
        parse.error("--implant requires both --in-file and --out-file.")
        return

    if args.extract:
        image_path = args.extract

    if args.implant:
        image_path = args.implant

    steganography                       = Steganography(image_path)
    steganography.load_input_image()

    if args.in_file:
        input_file                      = args.in_file

    if args.out_file:
        output_file                     = args.out_file

    if args.extract:
        steganography.extract()

        if args.out_file:
            with open(output_file, "wb") as file_buffer:
                file_buffer.write(steganography.extracted_bytes)

        else:
            print(bytes(steganography.extracted_bytes))

    if args.implant:
        steganography.load_implant_data(input_file)
        steganography.get_implant_bits()
        steganography.set_implant_bits()
        steganography.save_steg_image(output_file)

if __name__ == "__main__":
    main()