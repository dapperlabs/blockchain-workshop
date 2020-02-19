from hashlib import sha256
import json
import time

START_DIFFICULTY = 4
BLOCK_TIME_IN_SECONDS = 5

class Transaction:
    def __init__(self, from_pubkey, to_pubkey, amount):
        self.from_pubkey = from_pubkey
        self.to_pubkey = to_pubkey
        self.amount = amount
    
class Block:
    def __init__(self, height, difficulty, previous_hash, transactions, timestamp):
        self.height = height        
        self.difficulty = difficulty
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp
        self.nonce = 0

    def __str__(self):
        return 'block %d {diff=%d, previous_hash=%s, timestamp=%s, nonce=%d, transactions=%s}' % (
            self.height, self.difficulty, self.previous_hash, self.timestamp, self.nonce, self.transactions)

    def compute_hash(self):
        return sha256(str(self).encode()).hexdigest()
    
    def difficulty_to_target(self):        
        return format((2**256 - 1) >> self.difficulty, '064x')

class Blockchain:    

    def __init__(self):
        self.blocks = []        
        self.difficulty = START_DIFFICULTY

        genesis_block = Block(1, self.difficulty, '0', [], time.time())    
        genesis_block.hash = genesis_block.compute_hash()    
        self.blocks.append(genesis_block)
        
    def __str__(self):
        return '\n ⛓ \n'.join(map(str, self.blocks))
    
    def get_last_block(self):
        return self.blocks[-1]
    
    def add_block(self, block):  
        block_hash = block.compute_hash()

        correct_difficulty = self.compute_next_difficulty()
        
        if block.previous_hash != self.get_last_block().hash:
            return False
        if not block_hash < block.difficulty_to_target():
            return False
        if block.difficulty != correct_difficulty:
            return False
        
        block.hash = block_hash
        
        self.blocks.append(block)
        
        return True
    
    def compute_next_difficulty(self):        
        if len(self.blocks) > 1:
            block_time_diff = self.get_last_block().timestamp - self.blocks[-2].timestamp                            
            if block_time_diff < BLOCK_TIME_IN_SECONDS:
                return self.get_last_block().difficulty + 1
            else:
                return self.get_last_block().difficulty - 1
        else:
            return START_DIFFICULTY

def from_dump(chain_dump):
    blockchain = Blockchain()

    for idx, block_fields in enumerate(chain_dump):
        block = Block(block_fields['height'],
                    block_fields['difficulty'],
                    block_fields['previous_hash'],
                    block_fields['transactions'],
                    block_fields['timestamp'])
        
        if idx > 0:
            added = blockchain.add_block(block)
            if not added:
                return False
        else:  
            blockchain.blocks.append(block)
    
    return blockchain
