import asyncio
from datetime import datetime
import logging
import time
import requests
from pytrends.request import TrendReq
from web3 import Web3
from web3.middleware import geth_poa_middleware
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables (if any)
from dotenv import load_dotenv
load_dotenv()

class StabilityIndexCalculator:
    def __init__(self):
        self.financial_health = 0
        self.community_engagement = 0
        self.stability_index = 0
        self.pytrends = TrendReq(hl='en-US', tz=360)
        # Ethereum setup
        self.web3 = Web3(Web3.HTTPProvider(os.getenv('ETH_NODE_URL')))
        # If using a testnet like Rinkeby or Goerli, inject the PoA middleware
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.account = self.web3.eth.account.from_key(os.getenv('PRIVATE_KEY'))
        self.oracle_address = Web3.to_checksum_address(os.getenv('ORACLE_ADDRESS'))
        self.oracle_abi = [...]  # Replace with the ABI of the StabilityOracle contract
        self.oracle_contract = self.web3.eth.contract(address=self.oracle_address, abi=self.oracle_abi)

    def fetch_financial_data(self):
        EIN = '<EIN>'  # Replace with the actual EIN
        api_url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{EIN}.json"
        try:
            response = requests.get(api_url)
            data = response.json()
            filings = data.get('filings_with_data')
            if filings and len(filings) > 0:
                revenue = filings[0].get('totrevenue', 0)
                expenses = filings[0].get('totfuncexpns', 0)
                if revenue > 0:
                    self.financial_health = (revenue - expenses) / revenue * 100
                else:
                    self.financial_health = 0
            else:
                self.financial_health = 0
            logger.info(f"Financial Health: {self.financial_health}")
        except Exception as e:
            logger.error(f"Error fetching financial data: {e}")
            self.financial_health = 0

    def fetch_community_engagement_data(self):
        try:
            self.pytrends.build_payload(kw_list=["Catholic Church"], timeframe='now 1-m')
            trends_data = self.pytrends.interest_over_time()
            if not trends_data.empty:
                self.community_engagement = trends_data["Catholic Church"].mean()
            else:
                self.community_engagement = 50  # Default value
            logger.info(f"Community Engagement: {self.community_engagement}")
        except Exception as e:
            logger.error(f"Error fetching community engagement data: {e}")
            self.community_engagement = 50  # Default value

    def calculate_stability_index(self):
        # Ensure the metrics are within expected ranges
        financial_weight = 0.6
        engagement_weight = 0.4
        # Normalize the metrics if necessary
        financial_health_normalized = max(0, min(self.financial_health, 100))
        engagement_normalized = max(0, min(self.community_engagement, 100))
        # Calculate stability index
        self.stability_index = (
            financial_weight * financial_health_normalized +
            engagement_weight * engagement_normalized
        )
        logger.info(f"Calculated Stability Index: {self.stability_index}")

    def update_stability_oracle(self):
        try:
            stability_index_scaled = int(self.stability_index * 1e4)  # Scale to match Solidity precision
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            txn = self.oracle_contract.functions.setStabilityIndex(stability_index_scaled).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': self.web3.to_wei('50', 'gwei'),
            })
            signed_txn = self.account.sign_transaction(txn)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            logger.info(f"Sent transaction to update StabilityOracle: {tx_hash.hex()}")
            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                logger.info("StabilityOracle updated successfully.")
            else:
                logger.error("Transaction failed.")
        except Exception as e:
            logger.error(f"Error updating StabilityOracle: {e}")

    def update_stability_index(self):
        logger.info(f"Updating Stability Index on {datetime.now()}")
        # Fetch data
        self.fetch_financial_data()
        self.fetch_community_engagement_data()
        # Calculate stability index
        self.calculate_stability_index()
        # Update the StabilityOracle on the blockchain
        self.update_stability_oracle()

def main():
    calculator = StabilityIndexCalculator()
    while True:
        calculator.update_stability_index()
        # Sleep for 30 days (in seconds)
        time.sleep(30 * 24 * 60 * 60)

if __name__ == "__main__":
    main()