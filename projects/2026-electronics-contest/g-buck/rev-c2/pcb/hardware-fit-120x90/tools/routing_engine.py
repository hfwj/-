"""Two-layer, clearance-checked signal branches with off-pad vias only."""
from route_pending import find_path, connected
from route_driver_bottom import add_line
from pcb_common import *


class Router:
    def __init__(self,meta,docs,pcb,holes):
        self.meta,self.docs,self.pcb=meta,docs,pcb
        self.holes=[Point(x,y).buffer(1.6) for x,y in holes]
        self.refresh()

    def refresh(self):
        self.parts,self.pads,self.bodies,self.tracks=copper_geometry(self.meta,self.docs,self.pcb)
        self.vias=copper_vias(self.docs,self.pcb)
        self.fills=copper_fills(self.docs,self.pcb)

    def obstacles(self,net,layer):
        return [p['geometry'] for p in self.pads if p['net']!=net and layer in p['layers']]+[
            t['geometry'] for t in self.tracks if t['net']!=net and t['layer']==layer]+[
            v['geometry'] for v in self.vias if v['net']!=net]+[
            f['geometry'] for f in self.fills if f['net']!=net and f['layer']==layer]+self.holes

    def via_options(self,p,obstacles,width):
        if 2 in p['layers']:return [{'point':(p['x'],p['y']),'via':False}]
        options=[];detours=[]
        for radius in (.95,1.1,1.25,1.5,1.75,2.,2.5,3.):
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                pt=p['x']+dx*radius,p['y']+dy*radius
                g=Point(*pt).buffer(.3)
                if not box(.5,.5,119.5,89.5).covers(g):continue
                if any(g.distance(h)<.200001 for h in obstacles[1]+obstacles[2]):continue
                if any(g.distance(q['geometry'])<.2 for q in self.pads+self.vias):continue
                stub=LineString([(p['x'],p['y']),pt]).buffer(width/2)
                if any(stub.distance(h)<.205 for h in obstacles[1]):
                    detours.append(pt);continue
                options.append({'point':pt,'via':True,'stub':[(p['x'],p['y']),pt]})
        for pt in (detours[:8] if len(options)<4 else []):
            path=find_path(p,{'x':pt[0],'y':pt[1]},obstacles[1],width=width,max_expansions=1000)
            if path:options.append({'point':pt,'via':True,'stub':path})
        return options

    def route(self,a,b,key,width=.25,extra=None,force_branch=False):
        net=a['net'];assert net and net==b['net']
        if not force_branch and connected(a,b,self.pads,self.tracks,self.vias,self.fills):return {'already_connected':True}
        obstacles={l:self.obstacles(net,l)+(extra or {}).get(l,[]) for l in (1,2)}
        options=[]
        if 1 in a['layers'] and 1 in b['layers']:
            points=find_path(a,b,obstacles[1],width=width)
            if points:options.append((LineString(points).length,1,points,[]))
        direct=math.dist((a['x'],a['y']),(b['x'],b['y']))
        # Short top paths preserve bottom return area; investigate bottom only
        # for a blocked or substantially detoured top path.
        if not options or options[0][0]>direct*1.3+2:
            va=self.via_options(a,obstacles,width);vb=self.via_options(b,obstacles,width)
            combos=sorted(((math.dist(x['point'],y['point'])+3*(x['via']+y['via']),x,y)
                           for x in va for y in vb),key=lambda q:q[0])
            for _,x,y in combos[:16]:
                if x['via'] and y['via'] and math.dist(x['point'],y['point'])<.800001:continue
                points=find_path({'x':x['point'][0],'y':x['point'][1]},
                                 {'x':y['point'][0],'y':y['point'][1]},obstacles[2],width=width)
                if points:
                    ends=[(a,x),(b,y)]
                    cost=LineString(points).length+sum(math.dist((p['x'],p['y']),v['point'])+3 for p,v in ends if v['via'])
                    options.append((cost,2,points,ends))
                    break
        if not options:return None
        _,layer,points,ends=min(options,key=lambda q:q[0])
        for n,(s,t) in enumerate(zip(points,points[1:])):
            add_line(self.docs[self.pcb],key+':main:'+str(n),net,layer,s,t,width)
        new_vias=[]
        for n,(p,v) in enumerate(ends):
            if not v['via']:continue
            x,y=v['point']
            for sn,(s,t) in enumerate(zip(v['stub'],v['stub'][1:])):
                add_line(self.docs[self.pcb],key+':stub:'+str(n)+':'+str(sn),net,1,s,t,width)
            vid=uuid.uuid5(uuid.NAMESPACE_URL,key+':via:'+str(n)).hex[:16]
            assert ('VIA',vid) not in self.docs[self.pcb]
            self.docs[self.pcb]['VIA',vid]={'partitionId':'','groupId':0,'netName':net,'ruleName':'',
                'centerX':x/.0254,'centerY':y/.0254,'holeDiameter':.3/.0254,'viaDiameter':.6/.0254,
                'viaType':'NORMAL','topSolderExpansion':None,'bottomSolderExpansion':None,
                'locked':False,'unusedInnerLayers':[]}
            new_vias.append([x,y])
        self.refresh();assert connected(a,b,self.pads,self.tracks,self.vias)
        return {'net':net,'layer':layer,'width_mm':width,'points_mm':points,
                'via_centers_mm':new_vias,'length_mm':LineString(points).length}
