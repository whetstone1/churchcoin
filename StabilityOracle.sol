// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/Ownable.sol";

contract StabilityOracle is Ownable {
    uint256 public constant STABILITY_PRECISION = 1e6;
    uint256 public stabilityIndex;

    event StabilityIndexUpdated(uint256 newIndex);

    function setStabilityIndex(uint256 _stabilityIndex) external onlyOwner {
        require(_stabilityIndex > 0 && _stabilityIndex <= STABILITY_PRECISION * 2, "Invalid stability index");
        stabilityIndex = _stabilityIndex;
        emit StabilityIndexUpdated(_stabilityIndex);
    }

    function getStabilityIndex() external view returns (uint256) {
        return stabilityIndex;
    }
}