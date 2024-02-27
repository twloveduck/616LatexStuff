import dataclasses
import enum
import typing
import weakref

stateRefType = weakref.ReferenceType[typing.Type['State']]
fsaRefType = weakref.ReferenceType[typing.Type['FSA']]

epsilonElement = '\epsilon'


# \csdef{STATE}#1{q_{#1}}
# \csdef{TRNS}#3{\t{\STATE{#1} \mapsto{#2} \STATE{#3}}}
# \csdef{MAKEMACHINE}#2{%
#     % 1 is prefix.%
#     % 2 is transitions.%
#     \
#     M_{#1} = \t{\s{\STATE{#1.0}, \STATE{#1.f}}, \Sigma, \s{#2}, \STATE{#1.0}, \s{\STATE{#1.f}}}%
# }


@dataclasses.dataclass
class Edge:
    fromState: stateRefType
    toState: stateRefType
    onElements: typing.Set[str]


# edgeRefType = weakref.ReferenceType[typing.Type[Edge]]

@dataclasses.dataclass
class State:
    parent: fsaRefType
    name: str
    edges: typing.List[Edge] = dataclasses.field(default_factory=list)


class NAME_MODES(enum.IntEnum):
    NUMERIC = 0
    GREEK = 1

    def next(self, mode: int) -> 'NAME_MODES':
        if mode == NAME_MODES.GREEK:
            return self.NUMERIC
        else
            return self.GREEK


@dataclasses.dataclass
class FSA:
    name: str
    initialState: State = dataclasses.field(default=None)
    finalState: State = dataclasses.field(default=None)
    nameMode: NAME_MODES = dataclasses.field(default_factory=NAME_MODES.NUMERIC)
    states: typing.List[State] = dataclasses.field(default_factory=list)
    _head: State = dataclasses.field(default_factory=None)
    _tail: State = dataclasses.field(default_factory=None)

    @classmethod
    def nextName(cls) -> str:

    def __post_init__(self):
        if self.initialState is None:
            self.initialState = State(weakref.ref(self), '0')
        if self.finalState is None:
            self.finalState = State(weakref.ref(self), 'f')
        self._head = weakref.ref(self.initialState)
        self._tail = weakref.ref(self.finalState)

    def __add__(self, other) -> 'FSA':
        retVal = FSA(self.name, self.initialState, self)
        self.initialState.edges.append(
                Edge(fromState=weakref.ref(self.initialState), toState=weakref.ref(machine.initialState),
                     onElements={epsilonElement}))
