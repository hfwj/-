"""Layer transitions must be physical; a net name is not a connection."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pcb_common import Point, LineString, Polygon, copper_fills
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


if __name__=='__main__':
    unittest.main()
