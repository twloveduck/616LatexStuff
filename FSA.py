
import dataclasses
import re
import string
import sys
import typing
import weakref

import pyperclip

# TO start thinking about
#
# flowchart LR
#
# linkStyle default background-color:red,stroke-width:2px,color:blue;
#
#     q0(("$$q_0$$"))
#   q1(("$$q_1$$"))
#   q2(("$$q_2$$"))
#   qf((("$$q_f$$")))
#
#     q0 -->|a| q0
#     q1 -->|a| q1
#     q2 -->|a| q2
#     qf -->|a| qf
#
#     q0 -->|b,c| q1
#     q1 -->|b,c| q2
#     q2 -->|b,c| qf
#     qf --->|b,c| q1
#
# M1((start)) --> q0
#
#
# classDef state fill:#dde,stroke:#00f,stroke-width:2px;
# classDef mach fill:#fff,stroke:#fff;
#
# class q0,q1,q2,qf state
#
# class M1 mach

stateRefType = weakref.ReferenceType[typing.Type['State']]
fsaRefType = weakref.ReferenceType[typing.Type['FSA']]

eps_ele = '\\epsilon'

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

@dataclasses.dataclass
class State:
    prefix: str
    idx: int | str

    @classmethod
    def sort_list(cls, states: list[str]) -> list[str]:
        return [str(q) for q in sorted([State.from_string(s_q) for s_q in states])]
    @classmethod
    def from_string(cls, s: str) -> 'State':
        # return f"{preprefix}q^{Brace(self.prefix)}_{Brace(str(self.idx))}{postfix}"
        mtch = re.match(r"\s?q\^\{([\w, \\]+)\}_\{(\w)\}\s?",s)
        if not mtch:
            raise ValueError(f"The state '{s}' does not seem to match the standard formatting.")
        return State(mtch.group(1), mtch.group(2))

    def __str__(self):
        """
        Returns a string representing a state in a FSA where the FSA machine has the given prefix
        Regarding this instance's idx:
            If it is 'f', then a space is appended (doesn't affect output) to denote
            it is an accepting state.
            If it is a 0 or '0' a space is prefixed to denote an initial state.
        :return: A string representing the name of a state in the FSA machine.
        """
        # return f"q_{'{'}{prefix}.{idx}{'}'}"
        preprefix = ''
        postfix = ''
        if self.idx == 'f':
            postfix = ' '
        if self.idx == 0 or self.idx == '0':
            preprefix = ' '

        # IF ANYTHING CHANGES HERE IT MUST CHANGE IN FROM STRING!
        return f"{preprefix}q^{Brace(self.prefix)}_{Brace(str(self.idx))}{postfix}"

    def __lt__(self, other: 'State') -> bool:
        # Final states are gt all other states.
        match (self.idx, other.idx):
            case ('f', 'f'):
                return self.prefix > other.prefix
            case ('f', _):
                return False
            case (_, 'f'):
                return True
            case _:
                return self.prefix < other.prefix
        # return self.prefix + '.' + str(self.idx) < other.prefix + '.' + str(other.idx)

def state(prefix: str, idx: int | str) -> str:
    """
    Returns a string representing a state in a FSA where the FSA machine has the given prefix
    :param prefix: FSA's prefix.
    :param idx: The index of this state in the FSA machine.
        If it is 'f', then a space is appended (doesn't affect output) to denote
        it is an accepting state.
        If it is a 0 or '0' a space is prefixed to denote an initial state.
    :return: A string representing the name of a state in the FSA machine.
    """
    return State(prefix, idx).__str__()
    # return f"q_{'{'}{prefix}.{idx}{'}'}"
    # preprefix = ''
    # postfix = ''
    # if idx == 'f':
    #     postfix = ' '
    # if idx == 0 or idx == '0':
    #     preprefix = ' '
    #
    # return f"{preprefix}q^{Brace(prefix)}_{Brace(str(idx))}{postfix}"


def state_2(name: str, idx: int | str) -> str:
    return state(idx_2(name), idx)


shortMachTemplate: string.Template = (
        string.Template(
                "\\begin{gather*}\n%\n% - $representation - \n\\textit{Machine description for $$M_{$name}$$}\\\\\n"
                # "\\\\~\\\\\n%\n% - $representation - \n\\textit{Machine description for $$M_{$name}$$}\\\\\n"
                "M_{$name} = \\t{Q_{$name}, \\Sigma, \\delta_{$name}, $q0, F_{$name}} = "
                "\\t{\\s{$states}, \\Sigma, \\s{$transitions}, $q0, \\s{$qf}}\n"
                "\\end{gather*}\n\n"
        ))

machTemplate: string.Template = (
        string.Template(
                "\\begin{gather*}\n%\n% - $representation - \n\\textit{Machine description for $$M_{$name}$$}\n"
                # "\\\\~\\\\\n%\n% - $representation - \n\\textit{Machine description for $$M_{$name}$$}\\\\\n"
                "$transitions \n"
                "M_{$name} = \\t{Q_{$name}, \\Sigma, \\delta_{$name}, $q0, F_{$name}} = "
                "\\t{\\s{$states}, \\Sigma, \\delta_{$name}, $q0, \\s{$qf}}\n"
                "\\end{gather*}\n\n"
        ))

longMachTemplate: string.Template = (
        string.Template(
                "\\begin{gather*}\n%\n% - $representation - \n\\textit{Machine description for $$M_{$name}$$}\\\\\n"
                "Q_{$name} = \\s{$states}\n"
                "$transitions "
                "F_{$name} = \\s{$qf}\\\\\n"
                "M_{$name} = \\t{Q_{$name}, \\Sigma, \\delta_{$name}, $q0, F_{$name}}\n"
                "\\end{gather*}\n\n"
        ))

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
        return f"{self.fromState}\\xmapsto{Brace(self.on)} {self.toState}"

    @classmethod
    def deltas_to_table(cls, deltaTable: list['Delta'], prefix: str) -> str:
        # q_{0-1} & \; & q_{e} &  q_{ne}\\ \hline
        # \ACC q_{e} & \; & q_{e} & q_{ne}\\ \hline
        # q_{ne} & \; & q_{e} & q_{ne}\\
        tableTemplate = string.Template(
                """\\end{gather*}
$$$$
\\begin{array}{|$colDec}
    \\hline
    \\delta_{$prefix} & \\; &  $eles  \\\\ \\hline
    $rows \\\\ \\hline
\\end{array}
$$$$
\\begin{gather*}
    """)
        sigma = set()
        states = set()
        fromToMap: dict[str, dict[str, list[str]|str]] = dict()
        # Add all element in the current alphabet to the list of elements.
        # Add all states to state list.
        for delta in deltaTable:
            if isinstance(delta.on, str):
                sigma.add(delta.on)
            else:
                sigma.update(delta.on)

            fromToMap[norm_st(delta.fromState)] = {'ORIG': delta.fromState}
            states.add(delta.fromState)
            states.add(delta.toState)

        # For states that are accepting they may not appear in the mapping.
        # This is used as a default empty mapping. This will ALWAYS happen in
        # an FSA constructed by Thompson's Construction Algorithm.
        blankKey: dict[str, list[str]] = dict([(ele, list()) for ele in sigma])
        # Could have done this all at once, but not concerned with speed, and
        # I believe there is some issue with set default and nested collections.
        for state in states:
            # Must do this before sorting because State.sort_list destroys
            # normalization.
            fromToMap.setdefault(norm_st(state), dict())['ORIG'] = state
            for ele in sigma:
                fromToMap[norm_st(state)][ele] = list()
        for delta in deltaTable:
            if isinstance(delta.on, str):
                fromToMap[norm_st(delta.fromState)][delta.on].append(delta.toState)
            else:
                for ele in delta.on:
                    fromToMap[norm_st(delta.fromState)][ele].append(delta.toState)

        sigma = sorted(list(sigma))
        states = State.sort_list(states)
        accepting = lambda state: '\\ACC ' if state[-1] == ' ' else ''
        return tableTemplate.substitute(
                prefix=prefix,
                colDec='|'.join(list((len(sigma) + 3) * 'c')),
                eles=' & '.join(list(sigma)),
                rows='\\\\ \\hline\n  '.join(
                        [accepting(fromToMap[norm_st(state)]['ORIG']) + state + " & \\; & " + " & ".join(
                                [', '.join(fromToMap[norm_st(state)][ele]) for ele in sigma])
                         for state in states]))


transitions_type = (list[tuple[int | str, onType, int | str] | Delta] | onType)

TRIM_COMPOSED_ACC_STATES = True
norm_st = lambda state: state

# The following aid in normalization (removing start and accept states from
# composed machines (unions, concatenations)
if TRIM_COMPOSED_ACC_STATES:
    norm_st = lambda state: state.strip()

state_2norm = lambda *state: norm_st(state_2(*state))

@dataclasses.dataclass
class Machine:
    name: str
    transitions: transitions_type

    def to_mermaid(self) -> str:
        deltas = []
        states = set()
        for delta in self.__normalize().transitions:
            deltas.append((State.from_string(delta.fromState), delta.on, State.from_string(delta.toState)))
            states.add(delta.fromState)
            states.add(delta.toState)
        qStates = [State.from_string(sq) for sq in states]
        nodes = '\n'.join([f'  q{q.idx}(("$$q_{q.idx}$$"))' for q in qStates])
        return f"""
flowchart LR
    {nodes}
        """

    def __str__(self) -> str:
        return getMachineStr(self.name, self.transitions)
    def __normalize(self) -> 'Machine':
        """
        This returns a new machine with all the same transitions as this machine,
        but with all transitions as Delta instances.
        :see: Delta
        :return: A new machine identical to this one.
        """
        global TRIM_COMPOSED_ACC_STATES

        deltasTable: list[Delta] = []
        prefix = idx_2(self.name)
        match self.transitions:
            # Determine which type of transition it is and handle it.
            case [*deltas]:
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

                            fromName = match_to_state(fromIdx)
                            toName = match_to_state(toIdx)
                            deltasTable.append(Delta(fromName, on, toName))
                        case transition if isinstance(transition, Delta):
                            # states.add(transition.fromState)
                            # states.add(transition.toState)
                            deltasTable.append(transition)
                        case _:
                            raise ValueError(f"No match found for {delta}.")
            case str(on):
                # states.add(fromName := state(prefix, 0))
                # states.add(toName := state(prefix, 0))
                deltasTable.append(Delta(state(prefix, 0), on, state(prefix, 0)))
            case _:
                raise ValueError(f"No match found for {self.transitions}.")

        if TRIM_COMPOSED_ACC_STATES:
            for delta in deltasTable:
                delta.fromState = norm_st(delta.fromState)
                delta.toState = norm_st(delta.toState)
        # print(deltasTable)
        return Machine(self.name, deltasTable)

    def setName(self, name: str) -> 'Machine':
        """
        This allows the user to set the machine name. It allows for chaining
        such that you could do the following:
        Examples:
            M3 = (M1 + M2).setName('Bob')
            M4 = M1.concat(M2).setName('Tom')
            M5 = M1.KStar().setName('M1s')
        :param name: The name of the machine
        :return: This machine.
        """
        self.name = name
        return self

    def __add__(self, other: 'Machine') -> 'Machine':
        """
        This performs FSA union under Thompson's Construction Algorithm.
        :param other: The other machine to union with this machine.
        :return: A new machine constructed as per Thompson's Construction Algorithm.
        """
        # This is a union. Return a machine with a new init state with ε
        # transitions to my and other init states. Add a new final state that
        # has ε transitions from my and other final states.
        return Machine('Undefined', [
                (0, eps_ele, state_2norm(self.name, 0)),
                (0, eps_ele, state_2norm(other.name, 0)),
                *self.__normalize().transitions, *other.__normalize().transitions,
                (state_2norm(other.name, 'f'), eps_ele, 'f'),
                (state_2norm(self.name, 'f'), eps_ele, 'f')
        ])

    def concat(self, other: 'Machine') -> 'Machine':
        """
        This performs FSA concatenation under Thompson's Construction Algorithm.
        :param other: The other machine to union with this machine.
        :return: A new machine constructed as per Thompson's Construction Algorithm.
        """
        # This is a concatenation. Return a machine with a new init state with ε
        # transitions to my init state. Add a transition from my final to other
        # init state.  Add a new final state that
        # has ε transition from other final state.
        return Machine('Undefined', [
                (0, eps_ele, state_2norm(self.name, 0)),
                *self.__normalize().transitions,
                (state_2norm(self.name, 'f'), eps_ele, state_2(other.name, '0')),
                *other.__normalize().transitions,
                (state_2norm(other.name, 'f'), eps_ele, 'f')
        ])

    def KStar(self) -> 'Machine':
        """
        This performs FSA Kleene star under Thompson's Construction Algorithm.
        :param other: The other machine to union with this machine.
        :return: A new machine constructed as per Thompson's Construction Algorithm.
        """
        # This is a Kleene star. Technically there should be new start and a single
        # accepting state added, but as these are constructed with only single start
        # and end states it would be superfluous. Return a machine with a new  ε
        # transition from my final state to my init state.
        return Machine(self.name + "'", [
                *self.transitions,
                ('f', eps_ele, 0)
        ])


def getMachine(name: str, transitions: transitions_type) -> tuple[str, Machine]:
    assert name != 'Undefined'
    states: set[str] = set[str]()
    deltasTable: list[Delta] = []
    prefix = idx_2(name)
    match transitions:
        # Determine which type of transition it is and handle it.
        case [*deltas]:
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
                                    raise ValueError(f"Unrecognized transition element {possIdx} in transition {delta}")

                        states.add(fromName := match_to_state(fromIdx))
                        states.add(toName := match_to_state(toIdx))
                        deltasTable.append(Delta(fromName, on, toName))
                    case transition if isinstance(transition, Delta):
                        states.add(transition.fromState)
                        states.add(transition.toState)
                        deltasTable.append(transition)
                    case _:
                        raise ValueError(f"No match found for {delta}.")
        case str(on):
            states.add(fromName := state(prefix, 0))
            states.add(toName := state(prefix, 'f'))
            deltasTable.append(Delta(fromName, on, toName))
        case _:
            raise ValueError(f"No match found for {transitions}.")
    xlist = ', '.join([str(delta) for delta in deltasTable])

    curMach = Machine(name, deltasTable)
    match len(states):
        case int(1 | 2):
            return (shortMachTemplate.substitute(representation=repr([name, transitions]),
                                                 name=prefix,
                                                 states=', '.join(State.sort_list(states)),
                                                 transitions=xlist,
                                                 q0=state(prefix, 0),
                                                 qf=state(prefix, 'f')), curMach)
        case int(3 | 4):
            return (machTemplate.substitute(representation=repr(curMach),
                                            name=prefix,
                                            states=', '.join(State.sort_list(states)),
                                            transitions=Delta.deltas_to_table(deltasTable, prefix),
                                            q0=state(prefix, 0),
                                            qf=state(prefix, 'f')), curMach)

        case _:
            return (longMachTemplate.substitute(representation=repr([name, transitions]),
                                                name=prefix,
                                                states=', '.join(State.sort_list(states)),
                                                transitions=Delta.deltas_to_table(deltasTable, prefix),
                                                q0=state(prefix, 0),
                                                qf=state(prefix, 'f')), curMach)

    # return (strResult, Machine(name, deltasTable))


def getMachineStr(name: str, transitions: transitions_type) -> str:
    return getMachine(name, transitions)[0]


# Tests
# print(state('\\alpha', 0))
# print(idx_2('a1b'))
# print(idx_2('a1b.0'))
# print(Delta(state('1', 0), 'a', state('1', 'f')))
# print(Delta(state('1', 0), ['a', epsilonElement], state('1', 1)))

outputStr = ''


def print_mach(*mach: getMachineStr.__annotations__, reset: bool = False) -> Machine:
    global outputStr
    if reset:
        outputStr = ''
    (curMach, curDeltas) = getMachine(*mach)
    # print(f"Machine {mach!r}:\n{curMach}\n\n")
    outputStr += curMach
    return curDeltas


# Test a bunch of error conditions.
testBadMachines = [['a', b'a'],
                   [b'a', 'a'],
                   ['b', [(0, 'f')]],
                   ['b', ['a', eps_ele]],
                   ]
for mach in testBadMachines:
    try:
        curMach = getMachineStr(*mach)
        print(f"ERROR!!! Machine {mach} -> Should have caused an exception, but didn't! Output: {curMach}.",
              file=sys.stderr)
    except Exception as e:
        # print(f"Good catch for machine{mach!r}: {e}")
        pass

print_mach('a', 'a')
print_mach('a2a', 'a')
print_mach('a2b', [(0, 'b', 1), (1, 'c', 'f')])
print_mach('a2', [(0, eps_ele, state_2('a2a', 0)), (state_2('a2b', 'f'), eps_ele, 'f')])

#  (a + bc)(a + b)*
# Ma2a = print_mach('a2a', 'b', reset=True)
# Ma2b = print_mach('a2b', 'c')
# Ma2 = Ma2a.concat(Ma2b).setName('a2')
# print_mach(Ma2.name, Ma2.transitions)
# Ma1 = print_mach('a1', 'a')
# Ma = (Ma1 + Ma2).setName('a')
# print_mach(Ma.name, Ma.transitions)
# Mb1 = print_mach('b1', 'a')
# Mb2 = print_mach('b2', 'b')
# Mb = (Mb1 + Mb2).KStar().setName('b')
# print_mach(Mb.name, Mb.transitions)
#
# # Note this is not printed in the stuff.
# fullM = Ma.concat(Mb).setName('')
# pyperclip.copy(outputStr)
mt6M = Machine('a', [
        (0, ['b','c'], 1),
        (0, ['a'], 0),
        (1, ['b','c'], 2),
        (1, ['a'], 1),
        (2, ['b','c'], 'f'),
        (2, ['a'], 2),
        ('f', ['a'], 'f'),
        ('f', ['b','c'], 1),
])
pyperclip.copy(str(mt6M))
print("Done!\n\n")