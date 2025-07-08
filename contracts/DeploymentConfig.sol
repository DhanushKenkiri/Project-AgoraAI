// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title Contract Deployment and Configuration
 * @notice Helper contract for deploying and configuring the DeFi and Tokenization contracts
 */

// Contract addresses on different networks (for reference)
library ChainlinkAddresses {
    // Ethereum Mainnet
    address constant ETH_USD_MAINNET = 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419;
    address constant BTC_USD_MAINNET = 0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c;
    address constant LINK_USD_MAINNET = 0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c;
    address constant VRF_COORDINATOR_MAINNET = 0x271682DEB8C4E0901D1a1550aD2e64D568E69909;
    bytes32 constant KEY_HASH_MAINNET = 0x8af398995b04c28e9951adb9721ef74c74f93e6a478f39e7e0777be13527e7ef;
    
    // Polygon Mainnet
    address constant ETH_USD_POLYGON = 0xF9680D99D6C9589e2a93a78A04A279e509205945;
    address constant BTC_USD_POLYGON = 0xc907E116054Ad103354f2D350FD2514433D57F6f;
    address constant MATIC_USD_POLYGON = 0xAB594600376Ec9fD91F8e885dADF0CE036862dE0;
    address constant VRF_COORDINATOR_POLYGON = 0xAE975071Be8F8eE67addBC1A82488F1C24858067;
    bytes32 constant KEY_HASH_POLYGON = 0x6e099d640cde6de9d40ac749b4b594126b0169747122711109c9985d47751f93;
    
    // Avalanche Mainnet
    address constant ETH_USD_AVALANCHE = 0x976B3D034E162d8bD72D6b9C989d545b839003b0;
    address constant BTC_USD_AVALANCHE = 0x2779D32d5166BAaa2B2b658333bA7e6Ec0C65743;
    address constant AVAX_USD_AVALANCHE = 0x0A77230d17318075983913bC2145DB16C7366156;
    address constant VRF_COORDINATOR_AVALANCHE = 0xd5D517aBE5cF79B7e95eC98dB0f0277788aFF634;
    bytes32 constant KEY_HASH_AVALANCHE = 0x06eb0e2ea7cca202fc7c8258397a36f33d6ecb9f1a6d7931d3508a3acefb8a1;
    
    // CCIP Router Addresses
    address constant CCIP_ROUTER_ETHEREUM = 0x80226fc0Ee2b096224EeAc085Bb9a8cba1146f7D;
    address constant CCIP_ROUTER_POLYGON = 0x3C3D92629A02a8D95D5CB9650fe49C3544f69B43;
    address constant CCIP_ROUTER_AVALANCHE = 0xF4c7E640EdA248ef95972845a62bdC74237805dB;
    
    // Chain Selectors for CCIP
    uint64 constant CHAIN_SELECTOR_ETHEREUM = 5009297550715157269;
    uint64 constant CHAIN_SELECTOR_POLYGON = 4051577828743386545;
    uint64 constant CHAIN_SELECTOR_AVALANCHE = 6433500567565415381;
}

/**
 * @title Deployment Configuration
 * @notice Configuration parameters for contract deployment
 */
contract DeploymentConfig {
    struct NetworkConfig {
        address ethUsdPriceFeed;
        address btcUsdPriceFeed;
        address linkUsdPriceFeed;
        address vrfCoordinator;
        bytes32 keyHash;
        address ccipRouter;
        uint64 chainSelector;
        uint64 vrfSubscriptionId;
    }
    
    mapping(string => NetworkConfig) public networkConfigs;
    
    constructor() {
        // Initialize network configurations
        networkConfigs["ethereum"] = NetworkConfig({
            ethUsdPriceFeed: ChainlinkAddresses.ETH_USD_MAINNET,
            btcUsdPriceFeed: ChainlinkAddresses.BTC_USD_MAINNET,
            linkUsdPriceFeed: ChainlinkAddresses.LINK_USD_MAINNET,
            vrfCoordinator: ChainlinkAddresses.VRF_COORDINATOR_MAINNET,
            keyHash: ChainlinkAddresses.KEY_HASH_MAINNET,
            ccipRouter: ChainlinkAddresses.CCIP_ROUTER_ETHEREUM,
            chainSelector: ChainlinkAddresses.CHAIN_SELECTOR_ETHEREUM,
            vrfSubscriptionId: 1 // This should be set to actual subscription ID
        });
        
        networkConfigs["polygon"] = NetworkConfig({
            ethUsdPriceFeed: ChainlinkAddresses.ETH_USD_POLYGON,
            btcUsdPriceFeed: ChainlinkAddresses.BTC_USD_POLYGON,
            linkUsdPriceFeed: ChainlinkAddresses.MATIC_USD_POLYGON,
            vrfCoordinator: ChainlinkAddresses.VRF_COORDINATOR_POLYGON,
            keyHash: ChainlinkAddresses.KEY_HASH_POLYGON,
            ccipRouter: ChainlinkAddresses.CCIP_ROUTER_POLYGON,
            chainSelector: ChainlinkAddresses.CHAIN_SELECTOR_POLYGON,
            vrfSubscriptionId: 1
        });
        
        networkConfigs["avalanche"] = NetworkConfig({
            ethUsdPriceFeed: ChainlinkAddresses.ETH_USD_AVALANCHE,
            btcUsdPriceFeed: ChainlinkAddresses.BTC_USD_AVALANCHE,
            linkUsdPriceFeed: ChainlinkAddresses.AVAX_USD_AVALANCHE,
            vrfCoordinator: ChainlinkAddresses.VRF_COORDINATOR_AVALANCHE,
            keyHash: ChainlinkAddresses.KEY_HASH_AVALANCHE,
            ccipRouter: ChainlinkAddresses.CCIP_ROUTER_AVALANCHE,
            chainSelector: ChainlinkAddresses.CHAIN_SELECTOR_AVALANCHE,
            vrfSubscriptionId: 1
        });
    }
    
    function getNetworkConfig(string memory network) external view returns (NetworkConfig memory) {
        return networkConfigs[network];
    }
}
