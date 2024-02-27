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
from builtins import int

import pyperclip

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


def idx_2(index: str) -> str:
    """
    This converts a name into a subscript for a FSA machine.

    Example: nameToSubscript('a2b') = '\\alpha2\\beta'
    :param index: the name to convert.
    :return: A string sutable for the FSA machine subscript.
    """
    return ''.join([GreekIndexes.setdefault(ele, ele) for ele in list(index)])


def state(prefix: str, idx: int | str) -> str:
    """
    Returns a string representing a state in a FSA where the FSA machine has the given prefix
    :param prefix: FSA's prefix.
    :param idx: The index of this state in the FSA machine.
    :return: A string representing the name of a state in the FSA machine.
    """
    return f"q^{Brace(prefix)}_{Brace(str(idx))}"
    # return f"q_{'{'}{prefix}.{idx}{'}'}"


def state_2(name: str, idx: int | str) -> str:
    return state(idx_2(name), idx)


machTemplate: string.Template = (
        string.Template(
                "M_{$name} = \\t{Q_{$name}, \\Sigma, \\delta_{$name}, $q0, F_{$name}} = "
                "\\t{\\s{$states}, \\Sigma, \\s{$transitions}, $q0, \\s{$qf}}\\\\\n"))

onType = str | typing.Iterable[str]

transitions_type = (list[tuple[int | str, onType, int | str]] | onType)


@dataclasses.dataclass
class Delta:
    fromState: str
    on: onType
    toState: str

    def __post_init__(self):
        if type(self.on) is not str:
            self.on = ', '.join(self.on)

    def __str__(self) -> str:
        return f"{self.fromState}\\xmapsto{Brace(self.on)} {self.toState}"

    @classmethod
    def from_tuples(cls, prefix: str, transitions: transitions_type) -> list['Delta']:
        deltasTable: list['Delta'] = []
        match transitions:
            # Determine which type of transition it is and handle it.
            case [*deltas]:
                # List of state transitions.
                for delta in deltas:
                    match delta:
                        case (fromIdx, onType as on, toIdx):
                            def match_to_state(possIdx: int | str) -> str:
                                match possIdx:
                                    case '0' | 'f' | int(_):
                                        # Add my prefix and create a state.
                                        return state(prefix, possIdx)
                                    case str():
                                        # This is already a fully formatted state.
                                        return possIdx
                                    case _:
                                        raise ValueError(
                                                f"Unrecognized transition element {possIdx} in transition {delta}")

                            # states.add(fromName := match_to_state(fromIdx))
                            # states.add(toName := match_to_state(toIdx))
                            fromName = match_to_state(fromIdx)
                            toName = match_to_state(toIdx)
                            deltasTable.append(Delta(fromName, on, toName))
                        case _:
                            raise ValueError(f"No match found for {delta}.")
            case str(on):
                # states.add(fromName := state(prefix, 0))
                # states.add(toName := state(prefix, 'f'))
                fromName = state(prefix, 0)
                toName = state(prefix, 'f')
                deltasTable.append(Delta(fromName, on, toName))
            case _:
                raise ValueError(f"No match found for {transitions}.")
        return deltasTable


@dataclasses.dataclass
class Machine:
    name: str
    transitions: transitions_type
    parentMachine: 'Machine' = dataclasses.field(default=None, init=False)
    nestLevel: int = dataclasses.field(default=None, init=False)
    prefix: str = dataclasses.field(default=None, init=False)
    deltasTable: list[Delta] = dataclasses.field(default_factory=list, init=False)
    states: set[str] = dataclasses.field(default_factory=set, init=False, repr=False)
    initComplete: bool = False

    # @classmethod
    # def __reset__(cls):
    @classmethod
    def __get_root_source__(cls):
        rootSrc = list('abcde')
        yield rootSrc.pop(0)

    def get_next_index(self):
        if self.nestLevel == 0:
            return self.__class__.__get_root_source__()
        else:
            source = list('abcde') if self.nestLevel % 2 == 0 else range(10)
            yield source.pop(0)#str(next(source))

    def __post_init__(self):
        if self.parentMachine is None:
            nestLevel = 0
        else:
            nestLevel = 0
            while parent := self.parentMachine is not None:
                nestLevel += 1
                parent = parent.parentMachine

    def do_init(self):
        if self.initComplete:
            return
        # if self.name is not None:
        #     self.prefix = self.name
        # else:
        #     self.name = next(self.parentMachine.get_next_index() if self.parentMachine else self.get_next_index())
        self.prefix = idx_2(self.name)

        deltasTable = Delta.from_tuples(self.prefix, self.transitions)

        for delta in deltasTable:
            self.states.add(delta.fromState)
            self.states.add(delta.toState)

    def __str__(self):
        self.do_init()

        xlist = ', '.join([str(delta) for delta in self.deltasTable])
        return machTemplate.substitute(name=self.prefix, transitions=xlist, q0=state(self.prefix, 0),
                                       qf=state(self.prefix, 'f'))

    # def __add__(self, other) -> 'Machine':
    #     # This is the union. New q0 epsilon transitions to lhs q_0 and rhs q_0.
    #     # New q_f is epsilon transitioned to from lhs&rhs q_f
    #
    #     retVal = Machine(self.transitions + other.transitions)
    #     self.parentMachine = retVal
    #     other.parentMachine = retVal
    #     return retVal

# def m_cat(name: str, lhs: transitions_type, rhs: transitions_type) -> transitions_type:


# Tests
print(state('\\alpha', 0))
print(idx_2('a1b'))
print(idx_2('a1b.0'))
print(Delta(state('1', 0), 'a', state('1', 'f')))
print(Delta(state('1', 0), ['a', epsilonElement], state('1', 1)))

outputStr = ''


def print_mach(mach: Machine, reset: bool = False):
    global outputStr
    if reset:
        outputStr = ''
    # mach
    print(f"Machine {mach!r}:\n{mach!s}\n\n")
    outputStr += str(mach)


# Test a bunch of error conditions.
testBadMachines = ['a1', ['a', epsilonElement],
                   ['a', b'a'],
                   [b'a', 'a'],
                   ['b', [(0, 'f')]],
                   ['b', ['a', epsilonElement]],
                   ]
for mach in testBadMachines:
    try:
        print(mach)
        print(Machine(*mach))
    except Exception as e:
        print(f"Good catch for machine{mach!r}: {e}")

print_mach(Machine('a', 'a'))
print_mach(Machine('a2a', 'a'))
print_mach(Machine('a2b', [(0, 'b', 1), (1, 'c', 'f')]))
print_mach('a2', [(0, epsilonElement, state_2('a2a', 0)), (state_2('a2b', 'f'), epsilonElement, 'f')])

#  (a + bc)(a + b)*
print_mach('a2a', 'b', reset=True)
print_mach('a2b', 'c')
print_mach('a2', [(0, epsilonElement, state_2('a2a', 0)), (state_2('a2b', 'f'), epsilonElement, 'f')])
print_mach('a1', 'a')
print_mach('a', [
        (0, epsilonElement, state_2('a1', 0)),
        (0, epsilonElement, state_2('a2', 0)),
        (state_2('a1', 'f'), epsilonElement, 'f'),
        (state_2('a2', 'f'), epsilonElement, 'f')
])

# def mach_cat(name: str, machAdeltas: transitions_type, machBdeltas: transitions_type):
#     print(machAdeltas)

pyperclip.copy(outputStr.strip())
