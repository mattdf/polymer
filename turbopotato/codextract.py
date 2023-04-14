import sys
import re
from typing import Generic, TypeVar, Optional, Type
from collections import defaultdict
from dataclasses import dataclass, field

# Reference: https://docs.soliditylang.org/en/latest/grammar.html

@dataclass
class _BaseInfo:
    name: str
    line_start:int
    line_end:int
    lines:list[str] = field(default_factory=list)
    def source(self, j='\n'):
        return j.join(self.lines)

class UnCaught(_BaseInfo):
    pass

@dataclass
class FunctionInfo(_BaseInfo):
    def signature(self):
        sig = re.match(r'\s*(?P<sig>(fallback|receive|constructor|function)[^;{]+)', self.source(' ')).group('sig')
        return re.sub(r'\s+', ' ', sig)

@dataclass
class ModifierInfo(_BaseInfo):
    pass

@dataclass
class EventInfo(_BaseInfo):
    def signature(self):
        sig = re.match(r'\s*(?P<sig>(event\s+)[^;]+)', self.source(' ')).group('sig')
        return re.sub(r'\s+', ' ', sig)

@dataclass
class ContractInfo(_BaseInfo):
    functions:list[FunctionInfo] = field(default_factory=list)
    events:list[EventInfo] = field(default_factory=list)
    using:list[str] = field(default_factory=list)
    types:list[str] = field(default_factory=list)
    modifiers:list[ModifierInfo] = field(default_factory=list)
    is_library:bool=False
    is_interface:bool=False
    is_contract:bool=True
    is_abstract:bool=False
    uncaught:list[UnCaught] = field(default_factory=list)

@dataclass
class ExtractedInfo(_BaseInfo):
    pragmas:list[str] = field(default_factory=list)
    imports:list[str] = field(default_factory=list)
    using:list[str] = field(default_factory=list)
    types:list[str] = field(default_factory=list)
    contracts:list[ContractInfo] = field(default_factory=list)

T = TypeVar('T')

class Collector(Generic[T]):
    def __init__(self, name:str, line_start:int, **extra):
        self.name = name
        self.line_start = line_start
        self.extra = extra
        self._ = defaultdict[str,list](list)
    def collect(self, cat:str, what):
        self._[cat].append(what)
    def finish(self, line_end, obj:Type[T], lines:list[str]):
        args = dict(
            name=self.name,
            line_start=self.line_start,
            line_end=line_end,
            lines=lines[self.line_start:line_end])
        for k, v in self._.items():
            args[k] = v
        args.update(self.extra)
        return obj(**args)

def analyze_lines(name, lines:list[str]):
    toplevel:Collector[ExtractedInfo] = Collector(name, 0)
    if not len(lines):
        return toplevel.finish(0, ExtractedInfo, lines)
    in_contract:Optional[Collector[ContractInfo]] = None
    in_function:Optional[Collector[FunctionInfo]] = None
    in_modifier:Optional[Collector[ModifierInfo]] = None
    in_event:Optional[Collector[EventInfo]] = None
    in_comment = False
    for i, line in enumerate(lines):        
        line = line.strip()
        if not in_comment and line.startswith('/*'):
            in_comment = True
            continue
        if in_comment:
            if '*/' in line:
                in_comment = False
                continue
            continue
        if not len(line):
            continue
        if line.startswith('//'):
            continue
        if line.startswith('pragma'):
            toplevel.collect('pragmas', line)
            continue
        if line.startswith('import'):
            toplevel.collect('imports', line)
            continue
        if line.startswith('using'):
            if in_contract:
                in_contract.collect('using', line)
            else:
                toplevel.collect('using', line)
            continue
        if line.startswith('type'):
            if in_contract:
                in_contract.collect('types', line)
            else:
                toplevel.collect('types', line)
            continue
        is_abstract = line.startswith('abstract')
        is_contract = line.startswith('contract') or is_abstract
        is_library = line.startswith('library')
        is_interface = line.startswith('interface')
        if any([is_contract, is_library, is_interface]):
            if in_contract:                    
                if in_function:
                    in_contract.collect('functions', in_function.finish(i-1, FunctionInfo, lines))
                    in_function = None
                elif in_modifier:
                    in_contract.collect('modifiers', in_modifier.finish(i-1, ModifierInfo, lines))
                    in_modifier = None
                elif in_event:
                    in_contract.collect('events', in_event.finish(i-1, EventInfo, lines))
                    in_event = None
                toplevel.collect('contracts', in_contract.finish(i-1, ContractInfo, lines))
                in_contract = None
            m = re.match(r'\s*(abstract contract|contract|library|interface)\s+([^\s{]+)', line)
            in_contract = Collector(m.group(2), i, is_abstract=is_abstract, is_contract=is_contract, is_library=is_library, is_interface=is_interface)
            continue
        if line.startswith('event'):
            if in_contract:
                if in_function:
                    in_contract.collect('functions', in_function.finish(i-1, FunctionInfo, lines))
                    in_function = None
                if in_modifier:
                    in_contract.collect('modifiers', in_modifier.finish(i-1, ModifierInfo, lines))
                    in_modifier = None
                if in_event:
                    in_contract.collect('events', in_event.finish(i-1, EventInfo, lines))
                    in_event = None
                m = re.match(r'\s*event\s+([^\s{(]+)', line)
                in_event = Collector(m.group(1).strip(), i)
                continue
            raise RuntimeError(f'Cannot have event outside of contract! Line {i}: {line}')
        if line.startswith('modifier'):
            if in_contract:
                if in_modifier:
                    in_contract.collect('modifiers', in_modifier.finish(i-1, ModifierInfo, lines))
                    in_modifier = None
                elif in_function:
                    in_contract.collect('functions', in_function.finish(i-1, FunctionInfo, lines))
                    in_function = None
                elif in_event:
                    in_contract.collect('events', in_event.finish(i-1, EventInfo, lines))
                    in_event = None
                m = re.match(r'\s*modifier\s+([^\s{(]+)', line)
                in_modifier = Collector(m.group(1), i)
                continue
            raise RuntimeError(f'Cannot have modifier outside of contract! Line {i}: {line}')
        is_function = line.startswith('function')
        is_fallback = line.startswith('fallback')
        is_receive = line.startswith('receive')
        is_constructor = line.startswith('constructor')
        if any([is_fallback, is_receive, is_function, is_constructor]):
            if in_contract:                
                if in_modifier:
                    in_contract.collect('modifiers', in_modifier.finish(i-1, ModifierInfo, lines))
                    in_modifier = None
                if in_function:
                    in_contract.collect('functions', in_function.finish(i-1, FunctionInfo, lines))
                    in_function = None
                if in_event:
                    in_contract.collect('events', in_event.finish(i-1, EventInfo, lines))
                    in_event = None
                m = re.match(r'\s*(function|fallback|receive|constructor)\s*[({]?', line)
                if not m:                    
                    raise RuntimeError(f'Error parsing function on line: {line}')
                in_function = Collector(m.group(1).strip(), i)
                continue
            raise RuntimeError(f'Cannot have function outside of contract! Line {i}: {line}')
        if in_contract:
            if not any([in_function, in_modifier, in_event]):
                if not len(in_contract._['uncaught']) and line.strip() == '{':
                    continue
                in_contract.collect('uncaught', UnCaught(f'/*{i}*/ {line}', i, i, [line]))
    if in_event:
        in_contract.collect('events', in_event.finish(i, EventInfo, lines))
    if in_modifier:
        in_contract.collect('modifiers', in_modifier.finish(i, ModifierInfo, lines))
    if in_function:
        in_contract.collect('functions', in_function.finish(i, FunctionInfo, lines))
    if in_contract:
        toplevel.collect('contracts', in_contract.finish(i, ContractInfo, lines))
    return toplevel.finish(i, ExtractedInfo, lines)

def extract_file(filename:str=None,code:str=None):
    if filename is not None:
        with open(filename, 'r') as handle:
            code = handle.read()
    if code is not None:
        lines = code.splitlines()
    if code is None:
        raise RuntimeError("No code specified!")
    return analyze_lines(filename, lines), lines

def main(argv:list[str]):
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <filename.sol>")
        return 2
    info, lines = extract_file(argv[1])
    if len(info.pragmas):
        print('Pragmas:')
        for p in info.pragmas:
            print('\t', p)    
        print()
    if len(info.imports):
        print('Imports:')
        for i in info.imports:
            print('\t', i)
        print()
    print('Contracts:')
    for _ in info.using:   print('\t', _)
    for _ in info.types:   print('\t', _)
    for c in info.contracts:
        if c.uncaught:
            print('\tUncaught!')
            for _ in c.uncaught:
                print('\t\t', _)
        print('\t', 'library' if c.is_library else 'contract', c.name, c.line_start, c.line_end)
        for _ in c.events:  print('\t\t', _)
        for _ in c.using:   print('\t\t', _)
        for _ in c.types:   print('\t\t', _)
        for f in c.functions:
            print('\t\t', f.signature())
            for i in range(f.line_start, f.line_end):
                print('\t\t\t', i, lines[i])
        for m in c.modifiers:
            print('\t\t', m.name, m.line_start, m.line_end)
            for i in range(m.line_start, m.line_end):
                print('\t\t\t', i, lines[i])
        print()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
