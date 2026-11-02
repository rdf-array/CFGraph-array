""" rdf-undef: an empty slot of a sequence yields no triple """
import unittest

from rdflib import Literal, URIRef

from CFGraph import CFGraph


class SlotTestCase(unittest.TestCase):
    def test_slot_is_not_an_element(self):
        g = CFGraph()
        g.parse(data="<http://x/s> <http://x/p> ( 1 undef ( 3 undef ) ) .", format="turtle")
        self.assertEqual({Literal(1), Literal(3)}, set(g.objects(URIRef("http://x/s"), URIRef("http://x/p"))))


if __name__ == '__main__':
    unittest.main()
