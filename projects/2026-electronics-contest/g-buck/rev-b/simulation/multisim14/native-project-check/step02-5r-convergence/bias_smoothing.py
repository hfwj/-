"""Explicit diagnostic regularization of two scoped TI IIB equations.

Not a vendor model update or a hardware recommendation. Original artifacts
remain intact. Use only within an identified model/metadata span.
"""
OLD_COMMENT = 'Interface adapter only; original TI model follows byte-for-byte.'


def patch_bias(text, width='0.0001', *, part='INA240'):
    assert width in ['0.001', '0.0001']
    assert part in ['INA240', 'INA181']
    assert text.count(OLD_COMMENT) == 1
    revised = text.replace(OLD_COMMENT,
        f'DIAGNOSTIC MODIFIED {part}: two IIB 5V SGN breakpoints use TANH, width={width} V; NOT the unchanged TI model.')
    for pin in ['INP', 'INN']:
        old = f'SGN(V({pin})-VCMBRK) - 1 + ABS(SGN(V({pin})-VCMBRK))'
        new = f'TANH((V({pin})-VCMBRK)/{width})'
        assert revised.count(old) == 1
        revised = revised.replace(old, new)
    return revised
