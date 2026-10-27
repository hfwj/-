"""Layer transitions must be physical; a net name is not a connection."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pcb_common import Point, LineString
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


if __name__=='__main__':
    unittest.main()
