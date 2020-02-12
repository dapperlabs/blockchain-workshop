
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
        self.blocks = []
        
        genesis_block = Block(0, '0', [])    
        genesis_block.hash = genesis_block.compute_hash()    
        self.blocks.append(genesis_block)
        
    def __str__(self):
        return '\n ⛓ \n'.join(map(str, self.blocks))
    
    def get_last_block(self):
        return self.blocks[-1]
    
    def add_block(self, block):  
        block_hash = block.compute_hash()       
        
        if block.previous_hash != self.get_last_block().hash:
            return False
        if not block_hash.startswith('0' * self.difficulty):
            return False
        block.hash = block_hash
        self.blocks.append(block)
        return True


def from_dump(chain_dump):
    blockchain = Blockchain()

    for idx, block_fields in enumerate(chain_dump):
        block = Block(block_fields['height'],
                    block_fields['previous_hash'],
                    block_fields['transactions'])
        
        if idx > 0:
            added = blockchain.add_block(block)
            if not added:
                return False
        else:  
            blockchain.blocks.append(block)
    
    return blockchain
