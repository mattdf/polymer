// SPDX-License-Identifier: MIT
pragma solidity ^0.7.0;

import "forge-std/Test.sol";

//REF: https://ethereum-blockchain-developer.com/027-exceptions/04-invariants-with-assert/

contract ContractTest is Test {
        Invariant InvariantContract;

function testInvariant() public {
 
    InvariantContract = new Invariant();
    InvariantContract.receiveMoney{value: 1 ether}();
    console.log("BalanceReceived:",InvariantContract.balanceReceived(address(this)));

    InvariantContract.receiveMoney{value: 18 ether}();
    console.log("testInvariant, BalanceReceived:",InvariantContract.balanceReceived(address(this)));
/*
That's only 553255926290448384 Wei, or around 0.553 Ether. Where is the rest? What happened?

We are storing the balance in an uint64. Unsigned integers go from 0 to 2^n-1, 
so that's 2^64-1 or 18446744073709551615. So, it can store a max of 18.4467... 
Ether. We sent 19 Ether to the contract. 
It automatically rolls over to 0. So, we end up with 19000000000000000000 - 18446744073709551615 -1 (the 0 value) = 553255926290448384.
*/


    }
  receive() payable external{}
}

contract Invariant{

    mapping(address => uint64) public balanceReceived;

    function receiveMoney() public payable {
        balanceReceived[msg.sender] += uint64(msg.value);
    }

    function withdrawMoney(address payable _to, uint64 _amount) public {
        require(_amount <= balanceReceived[msg.sender], "Not Enough Funds, aborting");

        balanceReceived[msg.sender] -= _amount;
        _to.transfer(_amount);
    }
}