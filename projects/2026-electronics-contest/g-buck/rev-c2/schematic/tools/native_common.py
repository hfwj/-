"""Read native EasyEDA history and recover this project's unrotated pin geometry."""
from pathlib import Path
import collections
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[2]
GBUCK = ROOT.parent
sys.path.insert(0, str(GBUCK/'rev-b/pcb/github-rework-120x90/tools'))
from read_native import read_project


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def attrs(objects):
    out = collections.defaultdict(dict)
    for (kind, _), b in objects.items():
        if kind == 'ATTR':
            out[b.get('parentId')][b['key']] = b.get('value')
    return out


def inventory(meta, docs, title):
    schemes = [u for u, d in docs.items() if meta[u]['docType']=='SCH'
               and d.get(('META','META'),{}).get('title')==title]
    assert len(schemes)==1, schemes
    scheme = schemes[0]
    pages = {u:d for u,d in docs.items() if meta[u]['docType']=='SCH_PAGE'
             and d.get(('META','META'),{}).get('schematic')==scheme}
    parts, pins = {}, []
    for page, objects in pages.items():
        a = attrs(objects)
        lines = [b for (kind,_),b in objects.items() if kind=='LINE']
        for (kind,cid),c in objects.items():
            if kind!='COMPONENT': continue
            assert c.get('rotation',0)==0 and not c.get('isMirror'), cid
            at = a[cid];ref=at['Designator']
            assert ref not in parts, ref
            parts[ref] = {'page':page,'id':cid,'body':c,'attrs':at}
            sym=docs[at['Symbol']];sa=attrs(sym)
            for (pk,pid),p in sym.items():
                if pk!='PIN' or p.get('partId')!=c['partId']:continue
                x=c['x']+p['x'];y=c['y']+p['y'];nets=set()
                for l in lines:
                    x0,y0,x1,y1=(l[k] for k in ('startX','startY','endX','endY'))
                    if (abs((x-x0)*(y1-y0)-(y-y0)*(x1-x0))<1e-6
                        and min(x0,x1)-1e-6<=x<=max(x0,x1)+1e-6
                        and min(y0,y1)-1e-6<=y<=max(y0,y1)+1e-6):
                        net=a[l['lineGroup']].get('NET')
                        if net:nets.add(net)
                assert len(nets)<=1,(ref,pid,nets)
                pins.append({'ref':ref,'pin':sa[pid]['Pin Number'],
                             'name':sa[pid].get('Pin Name',''),
                             'net':next(iter(nets)) if nets else '',
                             'page':page,'x':x,'y':y,
                             'local_x':p['x'],'local_y':p['y']})
    return scheme,pages,parts,pins
