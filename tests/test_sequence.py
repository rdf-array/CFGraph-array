""" RDF-: a collection `( ... )` is one sequence term (rdflib.term.Sequence); CFGraph
flattens it into one triple per element, nested sequences included, like it does the
legacy rdf:first/rdf:rest ladders. """
import unittest

from rdflib import URIRef, Literal
from rdflib.term import Sequence

from CFGraph import CFGraph

s = URIRef("http://a.example/s")
p = URIRef("http://a.example/p")
q = URIRef("http://a.example/q")
o = URIRef("http://a.example/o")


class SequenceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.g = CFGraph()
        self.g.parse(data=f'<{s}> <{p}> (1 (2 3) <{o}>) ; <{q}> () .', format="turtle")

    def test_the_graph_holds_sequence_terms(self):
        # the store holds two triples whose objects are sequence terms; the flattening is a view
        stored = [t for t, _ in self.g.store.triples((None, None, None), None)]
        self.assertEqual(2, len(stored))
        self.assertTrue(all(isinstance(o_, Sequence) for _, _, o_ in stored))

    def test_flattens_elements_and_nested_sequences(self):
        self.assertEqual({(s, p, Literal(1)), (s, p, Literal(2)), (s, p, Literal(3)), (s, p, o)},
                         set(self.g.triples((s, p, None))))
        self.assertEqual([], list(self.g.triples((s, q, None))), "an empty sequence has no elements")

    def test_finds_elements_by_object(self):
        self.assertEqual([(s, p, Literal(3))], list(self.g.triples((None, None, Literal(3)))))
        self.assertEqual({s}, set(self.g.subjects(None, o)))
