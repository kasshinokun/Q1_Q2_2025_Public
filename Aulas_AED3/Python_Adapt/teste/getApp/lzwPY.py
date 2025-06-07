import os
import time
import argparse

def compress(input_file_path, output_file_path):
    """Compress a file using LZW algorithm"""
    start_time = time.time()
    
    # Read the input file as bytes
    with open(input_file_path, 'rb') as f:
        data = f.read()
    
    # Initialize dictionary with all possible single bytes
    dictionary = {bytes([i]): i for i in range(256)}
    next_code = 256
    compressed_data = []
    w = bytes()
    
    for byte in data:
        c = bytes([byte])
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            compressed_data.append(dictionary[w])
            # Add wc to the dictionary
            dictionary[wc] = next_code
            next_code += 1
            w = c
    
    if w:
        compressed_data.append(dictionary[w])
    
    # Write compressed data to output file
    with open(output_file_path, 'wb') as f:
        # Write the number of dictionary entries first (for decompression)
        f.write(len(compressed_data).to_bytes(4, byteorder='big'))
        # Write each code as 2 bytes (can be adjusted for larger files)
        for code in compressed_data:
            f.write(code.to_bytes(2, byteorder='big'))
    
    end_time = time.time()
    original_size = os.path.getsize(input_file_path)
    compressed_size = os.path.getsize(output_file_path)
    ratio = (compressed_size / original_size) * 100
    
    print(f"Compression completed in {end_time - start_time:.2f} seconds")
    print(f"Original size: {original_size} bytes")
    print(f"Compressed size: {compressed_size} bytes")
    print(f"Compression ratio: {ratio:.2f}%")

def decompress(input_file_path, output_file_path):
    """Decompress a file using LZW algorithm"""
    start_time = time.time()
    
    # Read the compressed file
    with open(input_file_path, 'rb') as f:
        # Read the number of codes
        num_codes = int.from_bytes(f.read(4), byteorder='big')
        # Read all codes (2 bytes each)
        compressed_data = []
        for _ in range(num_codes):
            compressed_data.append(int.from_bytes(f.read(2), byteorder='big'))
    
    # Initialize dictionary with all possible single bytes
    dictionary = {i: bytes([i]) for i in range(256)}
    next_code = 256
    decompressed_data = bytearray()
    
    # First code must be in the initial dictionary
    w = dictionary[compressed_data[0]]
    decompressed_data.extend(w)
    
    for code in compressed_data[1:]:
        if code in dictionary:
            entry = dictionary[code]
        elif code == next_code:
            entry = w + w[:1]
        else:
            raise ValueError(f"Bad compressed code: {code}")
        
        decompressed_data.extend(entry)
        
        # Add w + entry[0] to the dictionary
        dictionary[next_code] = w + entry[:1]
        next_code += 1
        
        w = entry
    
    # Write decompressed data to output file
    with open(output_file_path, 'wb') as f:
        f.write(decompressed_data)
    
    end_time = time.time()
    print(f"Decompression completed in {end_time - start_time:.2f} seconds")

def main():
    parser = argparse.ArgumentParser(description="LZW File Compression/Decompression")
    parser.add_argument('mode', choices=['compress', 'decompress'], help="Mode: compress or decompress")
    parser.add_argument('input', help="Input file path")
    parser.add_argument('output', help="Output file path")
    
    args = parser.parse_args()
    
    if args.mode == 'compress':
        compress(args.input, args.output)
    else:
        decompress(args.input, args.output)

if __name__ == "__main__":
    main()