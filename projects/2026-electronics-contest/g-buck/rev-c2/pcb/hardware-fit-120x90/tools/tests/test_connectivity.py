"""Layer transitions must be physical; a net name is not a connection."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pcb_common import Point, LineString, Polygon, box, copper_fills, copper_geometry, pcb_export_references
from route_pending import connected


class ConnectivityTests(unittest.TestCase):
    def setUp(self):
        self.a = {'net':'A','geometry':Point(0,0).buffer(.3),'layers':[1]}
        self.b = {'net':'A','geometry':Point(4,0).buffer(.3),'layers':[1]}
        self.tracks = [
            {'net':'A','geometry':LineString([(0,0),(2,0)]).buffer(.125),'layer':1},
            {'net':'A','geometry':LineString([(2,0),(4,0)]).buffer(.125),'layer':2}]

    def test_identical_labels_without_copper_are_open(self):
        self.assertFalse(connected(self.a,self.b,[self.a,self.b],[]))

    def test_external_part_export_flag_must_keep_its_board_terminals(self):
        docs={'device':{('META','META'):{'attributes':{'Convert to PCB':'no','Add into BOM':'yes'}}}}
        parts={'R_PRE':{'attrs':{'Device':'device'}}}
        self.assertEqual(pcb_export_references(docs,parts),set())
        docs['device']['META','META']['attributes']['Convert to PCB']='yes'
        self.assertEqual(pcb_export_references(docs,parts),{'R_PRE'})

    def test_instance_override_controls_PCB_export(self):
        docs={'device':{('META','META'):{'attributes':{'Convert to PCB':'yes'}}}}
        parts={'R_PRE':{'attrs':{'Device':'device','Convert to PCB':'no'}}}
        self.assertEqual(pcb_export_references(docs,parts),set())

    def test_crossing_layers_are_not_connected(self):
        self.b['layers'] = [1,2]
        self.assertFalse(connected(self.a,self.b,[self.a,self.b],self.tracks))

    def test_via_bridges_layers_but_smd_endpoint_does_not(self):
        via = {'net':'A','geometry':Point(2,0).buffer(.3)}
        self.assertFalse(connected(self.a,self.b,[self.a,self.b],self.tracks,[via]))
        self.b['layers'] = [1,2]
        self.assertTrue(connected(self.a,self.b,[self.a,self.b],self.tracks,[via]))

    def test_wrong_net_via_cannot_bridge(self):
        self.b['layers'] = [1,2]
        via = {'net':'B','geometry':Point(2,0).buffer(.3)}
        self.assertFalse(connected(self.a,self.b,[self.a,self.b],self.tracks,[via]))

    def test_plane_does_not_connect_an_smd_on_the_other_layer(self):
        fill={'net':'A','layer':2,'geometry':Polygon([(-1,-1),(5,-1),(5,1),(-1,1)])}
        self.b['layers']=[1,2]
        self.assertFalse(connected(self.a,self.b,[self.a,self.b],[],fills=[fill]))
        self.a['layers']=[1,2]
        self.assertTrue(connected(self.a,self.b,[self.a,self.b],[],fills=[fill]))

    def test_native_solid_fill_preserves_clearance_holes(self):
        body={'layerId':2,'netName':'GND','fillStyle':'SOLID','width':0,
              'path':[[0,0,'L',100,0,100,100,0,100,0,0],
                      [25,25,'L',25,75,75,75,75,25,25,25]]}
        fill=copper_fills({'pcb':{('FILL','test'):body}},'pcb')[0]
        self.assertFalse(fill['geometry'].covers(Point(1.27,1.27)))
        self.assertTrue(fill['geometry'].covers(Point(.25,.25)))
        self.assertAlmostEqual(fill['geometry'].area,7500*.0254**2)

    def test_router_preserves_clearance_in_a_corridor_between_grid_rows(self):
        from types import SimpleNamespace
        from route_multilayer import search
        def pad(x,y,g,net,layers):
            return {'x':x,'y':y,'geometry':g,'net':net,'layers':layers}
        a=pad(20,20.7,Point(20,20.7).buffer(.25),'A',[1])
        b=pad(24,20.7,Point(24,20.7).buffer(.25),'A',[1])
        low=box(21.5,18.825,22.5,19.825)
        high=box(21.5,20.445,22.5,21.445)
        walls=[low,high,box(21.5,1,22.5,18.825),box(21.5,21.445,22.5,89)]
        router=SimpleNamespace(pads=[a,b,pad(22,19.325,low,'B',[1,2]),
                                    pad(22,20.945,high,'B',[1,2])],vias=[],
                               obstacles=lambda net,layer:walls)
        result=search(router,a,b,.2)
        self.assertIsNotNone(result)
        for layer,points in result[0]:
            copper=LineString(points).buffer(.1)
            self.assertTrue(all(copper.distance(g)>=.2-1e-7 for g in walls))

    def test_native_round_pad_uses_a_conservative_circle_without_square_corners(self):
        import json,math
        docs={'pcb':{('COMPONENT','c'):{'x':0,'y':0,'angle':0},
                     ('ATTR','a'):{'parentId':'c','key':'Designator','value':'J'},
                     ('ATTR','b'):{'parentId':'c','key':'Footprint','value':'fp'},
                     ('PAD_NET',json.dumps(['PAD_NET','c','x','p'])):{'padNet':'GND'}},
              'fp':{('PAD','p'):{'centerX':0,'centerY':0,'defaultPad':{
                  'padType':'ELLIPSE','width':2/.0254,'height':2/.0254},
                  'padAngle':0,'num':'1','layerId':12,'hole':None}}}
        _,pads,_,_=copper_geometry({},docs,'pcb');g=pads[0]['geometry']
        self.assertFalse(g.covers(Point(.9,.9)))
        self.assertGreaterEqual(g.area,math.pi)
        self.assertLess(g.area,math.pi+.01)
        for n in range(360):
            angle=math.radians(n)
            self.assertTrue(g.covers(Point(math.cos(angle),math.sin(angle))))

    def test_native_round_pad_ignores_stale_height_and_cannot_invent_a_layer_bridge(self):
        import json
        docs={'pcb':{('COMPONENT','c'):{'x':0,'y':0,'angle':0},
                     ('ATTR','a'):{'parentId':'c','key':'Designator','value':'J'},
                     ('ATTR','b'):{'parentId':'c','key':'Footprint','value':'fp'},
                     ('PAD_NET',json.dumps(['PAD_NET','c','x','p'])):{'padNet':'A'}},
              'fp':{('PAD','p'):{'centerX':0,'centerY':0,'defaultPad':{
                  'padType':'ELLIPSE','width':2/.0254,'height':4/.0254},
                  'padAngle':0,'num':'1','layerId':12,'hole':None}}}
        _,pads,_,_=copper_geometry({},docs,'pcb')
        self.assertFalse(pads[0]['geometry'].covers(Point(0,1.5)))
        a={'net':'A','geometry':Point(-3,1.5).buffer(.1),'layers':[1]}
        b={'net':'A','geometry':Point(3,0).buffer(.1),'layers':[2]}
        tracks=[{'net':'A','layer':1,'geometry':LineString([(-3,1.5),(0,1.5)]).buffer(.1)},
                {'net':'A','layer':2,'geometry':LineString([(0,0),(3,0)]).buffer(.1)}]
        self.assertFalse(connected(a,b,[a,b]+pads,tracks))


if __name__=='__main__':
    unittest.main()
