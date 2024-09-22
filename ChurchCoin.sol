// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/Ownable.sol";

interface IOracle {
    function getStabilityIndex() external view returns (uint256);
}

contract ChurchCoin is Ownable {
    string public constant name = "ChurchCoin";
    string public constant symbol = "CHC";
    uint8 public constant decimals = 18;

    uint256 private constant STABILITY_PRECISION = 1e6;
    uint256 private constant INITIAL_FRAGMENTS_SUPPLY = 1e6 * 10**decimals(); // Initial supply: 1 million tokens
    uint256 private constant TOTAL_GONS = type(uint256).max - (type(uint256).max % INITIAL_FRAGMENTS_SUPPLY);

    uint256 private _totalSupply;
    uint256 private _gonsPerFragment;

    mapping(address => uint256) private _gonBalances;
    mapping(address => mapping(address => uint256)) private _allowedFragments;

    IOracle public oracle;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event LogRebase(uint256 indexed epoch, uint256 totalSupply);
    event OracleUpdated(address indexed newOracle);

    constructor(IOracle _oracle) {
        require(address(_oracle) != address(0), "Invalid oracle address");
        oracle = _oracle;

        _totalSupply = INITIAL_FRAGMENTS_SUPPLY;
        _gonsPerFragment = TOTAL_GONS / _totalSupply;

        _gonBalances[msg.sender] = TOTAL_GONS;

        emit Transfer(address(0), msg.sender, _totalSupply);
    }

    // --- ERC20 Functions ---

    function totalSupply() public view returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address who) public view returns (uint256) {
        return _gonBalances[who] / _gonsPerFragment;
    }

    function transfer(address to, uint256 value) public returns (bool) {
        uint256 gonValue = value * _gonsPerFragment;
        _gonBalances[msg.sender] -= gonValue;
        _gonBalances[to] += gonValue;

        emit Transfer(msg.sender, to, value);
        return true;
    }

    function allowance(address owner_, address spender) public view returns (uint256) {
        return _allowedFragments[owner_][spender];
    }

    function approve(address spender, uint256 value) public returns (bool) {
        _allowedFragments[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) public returns (bool) {
        _allowedFragments[from][msg.sender] -= value;

        uint256 gonValue = value * _gonsPerFragment;
        _gonBalances[from] -= gonValue;
        _gonBalances[to] += gonValue;

        emit Transfer(from, to, value);
        return true;
    }

    // --- Rebase Functionality ---

    function rebase() external onlyOwner returns (uint256) {
        uint256 stabilityIndex = oracle.getStabilityIndex();
        require(stabilityIndex > 0, "Invalid stability index");

        uint256 prevTotalSupply = _totalSupply;
        _totalSupply = (prevTotalSupply * stabilityIndex) / STABILITY_PRECISION;

        _gonsPerFragment = TOTAL_GONS / _totalSupply;

        emit LogRebase(block.timestamp, _totalSupply);
        return _totalSupply;
    }

    // --- Oracle Management ---

    function setOracle(IOracle _oracle) external onlyOwner {
        require(address(_oracle) != address(0), "Invalid oracle address");
        oracle = _oracle;
        emit OracleUpdated(address(_oracle));
    }
}