from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Prompt:
    name:str
    cats:list[str]
    text:str
    vars:list[str]
    model:str|None = None    
    description:Optional[str] = None
    max_tokens:Optional[int] = None
    temperature:Optional[int] = None


PROMPTS:dict[str,Prompt] = dict()


def add_prompt(p:Prompt):
    PROMPTS[p.name] = p


add_prompt(Prompt(
    name='extract-type-1',
    description='Description goes here',
    cats=['extract'],
    vars=['CODE'],
    model='text-davinci-003',
    text='''
You are an expert Solidity smart contract auditor helping to classify Solidity smart contracts as part of a pipeline.
You will be provided with a Solidity smart contract, or excerpts of one.
Start with a step by step analysis of potential vulnerabilities.
Then output a Python function which categorizes the contract. The function must be called `categorize` and return a dictionary with the following structure:

 * METHOD NAME
    * VULNERABILITY CATEGORIES LIST

```solidity
$$CODE$$
```
'''))

add_prompt(Prompt(
    name='extract-type-2',
    cats=['extract'],
    vars=['CODE'],
    model='text-davinci-003',
    text='''
You are an expert Solidity smart contract auditor and formal model prover.
I am an expert in Solidity contracts, formal modelling and security analysis, it is not necessary to explain it to me, I just need your analysis.
Please briefly describe the Solidity code below, outlining the intent for each function and how a user could cause it to malfunction.

```solidity
$$CODE$$
```

In your response provide a Python function which returns the a list of the opposites of correctly working or how an attacker could cause the contract to malfunction.

```python
def tests():
    return [
        {
            'vulnerability_description': '...',
            'category': '...',
            'function': 'function_name',
            'tags': [],
        }
    ]
```
'''))

add_prompt(Prompt(
    name='z3-1',
    cats=['z3'],
    vars=['CODE'],
    model='text-davinci-003',
    text='''
You are a theorem proving and formal model checking expert for Solidity smart contracts to identify vulnerabilities that uses Z3,     PySMT and carefully crafted Solidity contracts to demonstrate vulnerabilities.
Do not make a judgement that the contract does not contain any vulnerabilities, you must provide a demonstration.
You must provide a Python function which creates a Z3 or PySMT model to test the vulnerability.
The function returns the parameters used demonstrate the bug, or `None` if the model is unsatisfied.

For Z3 use 256 bit `BitVec` to simulate Solidity's `uint` type.

```solidity
$$CODE$$
```

Wrap your python function in markdown code below your notes. The python function you provide must be callable without any arguments.
'''))

add_prompt(Prompt(
    name='solidity-reentrency',
    cats=['solidity', 'reentrency'],
    vars=['CODE'],
    model='text-davinci-003',
    text='''
You are a theorem proving and formal model checking expert for Solidity smart contracts to identify vulnerabilities that uses carefully crafted Solidity contracts to demonstrate vulnerabilities.
Do not make a judgement that the contract does not contain any vulnerabilities, you must provide a demonstration.
Please identify which of the functions in the following code has a re-entrency bug and how it can be triggered by another contract.
You must provide minimal Solidity contract which creates invokes the vulnerable method to exploit the reentrency bug.
If the vulnerable contract transfers Ether, your contract must implement a default payable function which calls the exploitable contract.

```solidity
$$CODE$$
```

Wrap your minimal Solidity contract in markdown code below your notes.
'''))
