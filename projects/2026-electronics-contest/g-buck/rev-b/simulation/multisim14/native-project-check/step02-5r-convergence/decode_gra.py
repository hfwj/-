"""Decode native Grapher hex doubles; verify bounds before using numeric data.

Extract the user's multivolume RAR with WinRAR/libarchive first. Work files
(GRA, expanded XML, complete NPZ) stay outside the repository.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
import dclimplode
import numpy as np
from build_diagnostics import ROOT


def decode(path, work, *, dataset='u4'):
    assert dataset in ['u4', 'q2-20261026']
    expected_title = ('5R REL001 U4 boundary observation 25ms' if dataset=='u4'
        else '5R IIB SMOOTH 0.1mV MODEL DIAGNOSTIC 100ms')
    expected_end = .0164408 if dataset=='u4' else .0249514
    requested_end = .025 if dataset=='u4' else .1
    work.mkdir(parents=True, exist_ok=True)
    data = path.read_bytes()
    magic = b'CompressedElectronicsWorkbenchXML'
    assert data.startswith(magic)
    expected = struct.unpack_from('<Q', data, len(magic))[0]
    assert 0 < expected < 500_000_000
    pos = len(magic) + 8
    total = chunks = 0
    xmlpath = work / 'grapher.xml'
    with xmlpath.open('wb') as stream:
        while pos < len(data):
            size, compressed = struct.unpack_from('<II', data, pos)
            assert 0 < size <= 900000 and 0 < compressed and pos+8+compressed <= len(data)
            decoder = dclimplode.decompressobj()
            block = decoder.decompress(data[pos+8:pos+8+compressed])
            assert decoder.eof and len(block) == size
            stream.write(block)
            total += size
            chunks += 1
            pos += 8+compressed
    assert total == expected and pos == len(data)
    xml = xmlpath.read_bytes()
    title = re.search(rb'TabName="&amp;ASC([^"]+)"', xml)[1].decode('ascii')
    assert title == expected_title
    arrays, traces = {}, []
    for match in re.finditer(rb'<CTrace\b.*?</CTrace>', xml, re.S):
        trace = match.group()
        head = trace[:trace.index(b'>')+1]
        attr = lambda key: re.search((key+'="([^"]+)"').encode(), head)[1].decode('ascii')
        name = attr('Name').removeprefix('&amp;ASC')
        assert name not in arrays
        assert all(float(attr(k)) == v for k,v in [
            ('XOffset',0),('YOffset',0),('XScaleFactor',1),('YScaleFactor',1)])
        xhex = re.search(rb'\bXData="([0-9A-F]+)"', trace)[1]
        yhex = re.search(rb'\bYData="([0-9A-F]+)"', trace)[1]
        assert len(xhex) % 16 == len(yhex) % 16 == 0
        x = np.frombuffer(bytes.fromhex(xhex.decode()), dtype='<f8')
        y = np.frombuffer(bytes.fromhex(yhex.decode()), dtype='<f8')
        assert len(x) == len(y) and np.isfinite(x).all() and np.isfinite(y).all()
        assert (np.diff(x) > 0).all()
        bounds = {k:float(attr(k)) for k in ['XMin','XMax','YMin','YMax']}
        for actual, field in [(x.min(),'XMin'),(x.max(),'XMax'),(y.min(),'YMin'),(y.max(),'YMax')]:
            assert np.isclose(actual,bounds[field],rtol=1e-14,atol=1e-15), (name,field)
        if 'time' not in arrays:
            arrays['time'] = x.copy()
        else:
            assert np.array_equal(arrays['time'], x)
        arrays[name] = y.copy()
        traces.append({'name':name,'points':len(x),'bounds':bounds,'last':float(y[-1])})
    assert len(traces) == 14
    if dataset=='u4':
        assert len(arrays['time']) == 519429
    assert abs(float(arrays['time'][-1])-expected_end) <= 5e-8
    np.savez(work / 'all_traces.npz', **arrays)
    summary = {'date':'2026-10-25' if dataset=='u4' else '2026-10-26','GRA_bytes':len(data),
        'GRA_sha256':hashlib.sha256(data).hexdigest(), 'expanded_XML_bytes':total,
        'DCL_chunks':chunks,'page_title':title,'traces':traces,
        'encoding':'little-endian binary64 hex attributes, verified against all 14 stored X/Y extrema',
        'common_time_axis_exactly_equal':True,'time_strictly_increasing':True,
        'all_values_finite':True,'all_offsets_zero_scales_one':True,
        'last_time_s':float(arrays['time'][-1]),'matches_native_log_end_time':True,
        'requested_end_s':requested_end,'native_requested_duration_completed':False}
    if dataset=='u4':
        summary.update(matches_native_log_16_4408ms=True,native_25ms_completed=False)
    filename='native_u4_gra_decode.json' if dataset=='u4' else '2026-10-26_native_q2_gra_decode.json'
    (ROOT/'results/data'/filename).write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='traces'},indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('gra',type=Path)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--dataset',choices=['u4','q2-20261026'],default='u4')
    args=parser.parse_args()
    decode(args.gra,args.work,dataset=args.dataset)
