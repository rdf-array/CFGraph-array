from typing import NamedTuple, Union, Tuple, Optional, Generator

from rdflib import Graph, URIRef, Literal, BNode, RDF
from rdflib.collection import Collection
from rdflib.exceptions import UniquenessError
from rdflib.term import Node, Sequence

QueryTriple = Tuple[Optional[URIRef], Optional[URIRef], Optional[Union[Literal, URIRef]]]

SUBJ = Union[URIRef, BNode]
PRED = URIRef
OBJ = Node

class RDFTriple(NamedTuple):
    s: SUBJ = None
    p: PRED = None
    o: OBJ = None


class CFGraph(Graph):
    """ Collection Flattening Graph

    Collections are returned as lists of triples.

    rdf-array: a collection ``( ... )`` is one sequence term (rdflib.term.Sequence), so a
    statement ``s p (e1 e2)`` is returned as ``s p e1`` and ``s p e2``; a sequence
    object that is an element of another is flattened too.  Legacy rdf:first/rdf:rest
    ladders are flattened as before.
    """

    def __init__(self, *args, **kwargs) -> None:
        self._inside = False
        super().__init__(*args, **kwargs)

    def triples(self,
                pattern: Optional[Union[QueryTriple, SUBJ]],
                pred: Optional[PRED]='',
                obj: Optional[OBJ]='') -> Generator[RDFTriple, None, None]:

        # Allow a tuple or a list of three items
        if pattern is None or pred != '' or obj != '':
            pattern = (pattern, pred, obj)
        if not self._inside:
            try:
                self._inside = True
                for s, p, o in super().triples(pattern):
                    if isinstance(o, Sequence):
                        for e in _flatten(o):
                            yield (s, p, e)
                    elif o != RDF.nil:
                        if p not in (RDF.first, RDF.rest):
                            if isinstance(o, BNode):
                                if self.value(o, RDF.first, None):
                                    for e in Collection(self, o):
                                        yield(s, p, e)
                                else:
                                    yield (s, p, o)
                            else:
                                yield (s, p, o)
                        elif p == RDF.first and not pattern[0] and pattern[2]:
                            sp = self._list_root(s)
                            if sp:
                                yield (sp[0], sp[1], o)
                # rdf-array: an object pattern also matches the elements of sequence objects -- as the
                # rdf:first lookup above does for ladders, only when neither subject nor predicate is given
                if (pattern[2] is not None and pattern[2] != '' and not isinstance(pattern[2], Sequence)
                        and pattern[0] in (None, '') and pattern[1] in (None, '')):
                    for s, p, o in super().triples((pattern[0], pattern[1], None)):
                        if isinstance(o, Sequence) and pattern[2] in _flatten(o):
                            yield (s, p, pattern[2])
            finally:
                self._inside = False
        else:
            for t in super().triples(pattern):
                yield t

    def subjects(self, predicate: Optional[PRED]=None, object: Optional[OBJ]=None):
        for s, p in self.subject_predicates(object):
            if predicate is None or p == predicate:
                yield s

    def _list_root(self, n: BNode) -> Optional[Tuple[SUBJ, PRED]]:
        try:
            sps = list(self.subject_predicates(n))
            if len(sps) != 1:
                return None
            sp = sps[0]
            return sp if sp[1] != RDF.rest else self._list_root(sp[0])

        except UniquenessError:
            return None


def _flatten(seq: Sequence) -> Generator[Node, None, None]:
    """ rdf-array: the elements of a sequence, nested sequences flattened """
    for e in seq.elements:
        if isinstance(e, Sequence):
            yield from _flatten(e)
        else:
            yield e
