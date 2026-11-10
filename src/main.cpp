#include <iostream>
#include <fstream>
#include <vector>
#include <cstdint>

// Simple ATSC A/52 Frame Header Inspector / Decoder Stub
struct AC3Header {
    uint16_t syncword;
    uint16_t crc1;
    uint8_t fscod;
    uint8_t frmsizecod;
    uint8_t bsid;
    uint8_t bsmod;
    uint8_t acmod;
};

bool parse_ac3_header(const uint8_t* buffer, AC3Header& hdr) {
    hdr.syncword = (buffer[0] << 8) | buffer[1];
    if (hdr.syncword != 0x0B77) {
        return false;
    }
    hdr.fscod = (buffer[4] >> 6) & 0x03;
    hdr.frmsizecod = buffer[4] & 0x3F;
    hdr.bsid = (buffer[5] >> 3) & 0x1F;
    hdr.bsmod = buffer[5] & 0x07;
    hdr.acmod = (buffer[6] >> 5) & 0x07;
    return true;
}

int main(int argc, char* argv[]) {
    std::cout << "=============================================" << std::endl;
    std::cout << "  ATSC A/52 (AC-3 / E-AC-3) Decoder & Player " << std::endl;
    std::cout << "=============================================" << std::endl;

    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " <input_file.ac3>" << std::endl;
        return 1;
    }

    std::ifstream file(argv[1], std::ios::binary);
    if (!file) {
        std::cerr << "Error: Could not open file " << argv[1] << std::endl;
        return 1;
    }

    uint8_t header_buf[7];
    file.read(reinterpret_cast<char*>(header_buf), 7);
    if (file.gcount() < 7) {
        std::cerr << "Error: File too short." << std::endl;
        return 1;
    }

    AC3Header hdr;
    if (parse_ac3_header(header_buf, hdr)) {
        std::cout << "[+] Valid AC-3 Syncword (0x0B77) detected!" << std::endl;
        std::cout << "    - BSID (Bitstream ID): " << (int)hdr.bsid << std::endl;
        std::cout << "    - Sample Rate Code (fscod): " << (int)hdr.fscod << std::endl;
        std::cout << "    - Frame Size Code (frmsizecod): " << (int)hdr.frmsizecod << std::endl;
        std::cout << "    - Audio Coding Mode (acmod): " << (int)hdr.acmod << std::endl;
    } else {
        std::cout << "[-] Invalid AC-3 header / Syncword not found." << std::endl;
    }

    return 0;
}
