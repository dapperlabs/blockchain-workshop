
from hashlib import sha256
import json


class Block:
    def __init__(self, height, previous_hash, transactions):
        self.height = height        
        self.previous_hash = previous_hash
        self.transactions = transactions

    def __str__(self):
        return json.dumps(self.__dict__, sort_keys=True)

    def compute_hash(self):
        return sha256(str(self).encode()).hexdigest()

class Blockchain:
    difficulty = 2

    def __init__(self):
        self.blockchain = []
        
        genesis_block = Block(0, "0", [])    
        genesis_block.hash = genesis_block.compute_hash()    
        self.blockchain.append(genesis_block)        
    
    def __str__(self):
        return '\n ⛓ \n'.join(map(str, self.blockchain))
    
    def get_last_block(self):
        return self.blockchain[-1]
    
    def add_block(self, block):  
        block_hash = block.compute_hash()       
        
        if block.previous_hash != self.get_last_block().hash:
            return False
        if not block_hash.startswith('0' * self.difficulty):
            return False
        block.hash = block_hash
        self.blockchain.append(block)
        return True
