"""MCP4728 DS22187E Fig 5-8 byte encoding reference. No hardware I/O."""
import json

def multi_write(channel, code, gain):
    if channel not in range(4) or not 0 <= code <= 4095 or gain not in (1, 2):
        raise ValueError("invalid channel/code/gain")
    return [0x40 | (channel << 1), 0x80 | (0x10 if gain == 2 else 0) | (code >> 8), code & 255]

if __name__ == '__main__':
    a = multi_write(0, 1409, 2)
    b = multi_write(1, 1900, 1)
    assert a == [0x40, 0x95, 0x81]
    assert b == [0x42, 0x87, 0x6C]
    for channel in range(4):
        for gain in (1, 2):
            for code in (0, 1, 1409, 1900, 3089, 4095):
                f = multi_write(channel, code, gain)
                assert (f[0] & 6) >> 1 == channel
                assert ((f[1] & 15) << 8 | f[2]) == code
                assert bool(f[1] & 0x10) == (gain == 2)
                assert f[1] & 0x80 and not (f[1] & 0x60)
    print(json.dumps({'address_7bit': '0x60', 'A_internal_G2_code1409': a,
                      'B_internal_G1_code1900': b, 'hardware_test': 'NOT RUN',
                      'enable_rule': 'Hold RUN low until DAC write/readback and analog settling checks pass.'}, indent=2))
