import unittest
from blockchain import Transaction, Block, Blockchain
import time
from datetime import datetime
import jsonpickle

class TestTransactions(unittest.TestCase):
    def test_compute_hash(self):
        t = Transaction("from_key","to_key", 100)
        self.assertEqual(t.compute_hash(),
        "4001726425251de20236ca4a78d1a675b54c25ccfdc3f81ee1e9792d0b65f670")

genesis_ts = 1505346600
genesis_hash = "d275759bdcbcccd06605190acb94d1e46976a4bf5319403ee9d89e5bbacd9c00"
class TestBlock(unittest.TestCase):
    def test_compute_hash_genesis_block(self):
        genesis_block = Block(
            height=1, 
            difficulty=20,
            previous_hash='0',
            transactions=[],
            timestamp=genesis_ts)       
        self.assertEqual(genesis_block.compute_hash(), genesis_hash)

    def test_compute_hash_single_tx_block(self):
        tx_block = Block(
            height=2,
            difficulty=20,
            previous_hash = genesis_hash,
            transactions=[
                Transaction("from_key","to_key",100)
            ],
            timestamp = genesis_ts+10
        )
        self.assertEqual(tx_block.compute_hash(), 
        "be6f0432cf98e215f7211d7050c0f53f0e390e837853793735b31621f71dd87c")
        
if __name__ == '__main__':
    unittest.main()
