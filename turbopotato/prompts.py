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
You are an expert Solidity smart contractr auditor helping to classify Solidity smart contracts as part of a pipeline.
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
You are an expert Solidity smart contractr auditor and formal model prover.
I am an expert in Solidity contracts, formal modelling and security analysis, it is not necessary to explain it to me, I just need your analysis.
Please outlining the Solidity code below, very briefly outlining the intent for each function and how a user could cause it to malfunction.

```solidity
$$CODE$$
```

Provide your response as a Python function which returns the a list of the opposites of correctly working or how an attacker could cause the contract to malfunction.

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
You must provide Python functions which create a Z3 or PySMT model to test the vulnerability.
Each function returns the parameters used demonstrate the bug, or `None` if the model is unsatisfied.

For Z3 use 256 bit `BitVec` to simulate Solidity's `uint` type.

$$CODE$$
'''))
