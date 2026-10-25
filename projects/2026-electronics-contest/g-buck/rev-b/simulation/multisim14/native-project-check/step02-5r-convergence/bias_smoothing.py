"""Explicit diagnostic regularization of two INA240 IIB breakpoint equations.

Not a vendor model update or a hardware recommendation. Original artifacts
remain intact. Use only within an identified INA240 definition/metadata span.
"""
OLD_COMMENT = 'Interface adapter only; original TI model follows byte-for-byte.'


def patch_bias(text, width='0.0001'):
    assert width in ['0.001', '0.0001']
    assert text.count(OLD_COMMENT) == 1
    revised = text.replace(OLD_COMMENT,
        f'DIAGNOSTIC MODIFIED INA240: two IIB 5V SGN breakpoints use TANH, width={width} V; NOT the unchanged TI model.')
    for pin in ['INP', 'INN']:
        old = f'SGN(V({pin})-VCMBRK) - 1 + ABS(SGN(V({pin})-VCMBRK))'
        new = f'TANH((V({pin})-VCMBRK)/{width})'
        assert revised.count(old) == 1
        revised = revised.replace(old, new)
    return revised
