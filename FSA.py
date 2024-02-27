#
# @dataclasses.dataclass
# class Edge:
#     fromState: stateRefType
#     toState: stateRefType
#     onElements: typing.Set[str]
#
#
# # edgeRefType = weakref.ReferenceType[typing.Type[Edge]]
#
# @dataclasses.dataclass
# class State:
#     parent: fsaRefType
#     name: str
#     edges: typing.List[Edge] = dataclasses.field(default_factory=list)
#
#
# class NAME_MODES(enum.IntEnum):
#     NUMERIC = 0
#     GREEK = 1
#
#     def next(self, mode: int) -> 'NAME_MODES':
#         if mode == NAME_MODES.GREEK:
#             return self.NUMERIC
#         else
#             return self.GREEK
#
# @dataclasses.dataclass
# class FSA:
#     name: str
#     initialState: State = dataclasses.field(default=None)
#     finalState: State = dataclasses.field(default=None)
#     nameMode: NAME_MODES = dataclasses.field(default_factory=NAME_MODES.NUMERIC)
#     states: typing.List[State] = dataclasses.field(default_factory=list)
#     _head: State = dataclasses.field(default_factory=None)
#     _tail: State = dataclasses.field(default_factory=None)
#     _nextStateNum : typing.Optional[int] = 1
#
#     @classmethod
#     def nextName(cls) -> str:
#
#     def nextStateNum(self) -> int:
#         while True:
#             yield self._nextStateNum
#             self._nextStateNum += 1
#
#     def __post_init__(self):
#         if self.initialState is None:
#             self.initialState = State(weakref.ref(self), '0')
#         if self.finalState is None:
#             self.finalState = State(weakref.ref(self), 'f')
#         self._head = weakref.ref(self.initialState)
#         self._tail = weakref.ref(self.finalState)
#
#     def __add__(self, other) -> 'FSA':
#         retVal = FSA(self.name, self.initialState, self)
#         self.initialState.edges.append(
#                 Edge(fromState=weakref.ref(self.initialState), toState=weakref.ref(machine.initialState),
#                      onElements={epsilonElement}))
import dataclasses
import string
import typing
import weakref

# \csdef{STATE}#1{q_{#1}}
# \csdef{TRNS}#3{\t{\STATE{#1} \mapsto{#2} \STATE{#3}}}
# \csdef{MAKEMACHINE}#2{%
#     % 1 is prefix.%
#     % 2 is transitions.%
#     \
#     M_{#1} = \t{\s{\STATE{#1.0}, \STATE{#1.f}}, \Sigma, \s{#2}, \STATE{#1.0}, \s{\STATE{#1.f}}}%
# }

stateRefType = weakref.ReferenceType[typing.Type['State']]
fsaRefType = weakref.ReferenceType[typing.Type['FSA']]

epsilonElement = '\\epsilon'

GreekIndexes = {'a': '\\alpha', 'b': '\\beta',
                'c': '\\gamma', 'd': '\\zeta', 'e': '\\eta'}

[GreekIndexes.update({str(idx): str(idx)}) for idx in range(10)]


def Brace(s: str) -> str:
    return '{' + s + '}'


def state(prefix: str, idx: int | str) -> str:
    return f"q_{'{'}{prefix}.{idx}{'}'}"


def nameToSubscript(name: str) -> str:
    return ''.join([GreekIndexes.setdefault(ele, ele) for ele in list(name)])


machTemplate: string.Template = (
        string.Template(
                "M_{$name} = \\t{Q_{$name}, \\Sigma, \\delta_{$name}, $q0, F_{$name}} = "
                "\\t{\\s{$q0, $qf}, \\Sigma, \\s{$transitions}, $q0, \\s{$qf}}\\\\\n"))

onType = str | typing.Iterable[str]


@dataclasses.dataclass
class Delta:
    fromState: str
    on: onType
    toState: str

    def __post_init__(self):
        if type(self.on) is not str:
            self.on = ', '.join(self.on)

    def __str__(self) -> str:
        return f"{self.fromState}\\mapsto{Brace(self.on)} {self.toState}"


def Machine(name: str, transitions: (list[tuple[int, onType, int]: tuple[str, onType, str]] | onType)) -> str:
    states: set[str] = {}
    deltas: list[Delta] = []
    prefix = nameToSubscript(name)
    match transitions:
        case [*deltas]:
            for delta in deltas:
                match delta:
                    case (str(fromName), onType(on), str(toName)):
                        states.add(fromName)
                        states.add(toName)
                        deltas.append(Delta(fromName, on, toName))
                    case (str(fromIdx), onType(on), str(toIdx)):
                        states.add(fromName := state(prefix, fromIdx))
                        states.add(toName := state(prefix, toIdx))
                        deltas.append(Delta(fromName, on, toName))
                    case _:
                        raise ValueError(f"No match found for {delta}.")
        case str(on):
            states.add(fromName:= state(prefix, 0))
            states.add(toName:= state(prefix, 'f'))
            deltas.append(Delta(fromName, on, toName))
        case _:
            raise ValueError(f"No match found for {transitions}.")

    return machTemplate.substitute(name=prefix, q0=state(prefix, 0), qf=state(prefix, 'f'))

# Tests
print(state('\\alpha', 0))
print(nameToSubscript('a1b'))
print(nameToSubscript('a1b.0'))
print(Delta(state('1', 0), 'a', state('1', 'f')))
print(Delta(state('1', 0), ['a', epsilonElement], state('1', 1)))

