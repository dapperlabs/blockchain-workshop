from hashlib import sha256
import json
import time
import logging
import jsonpickle

logger = logging.getLogger()

START_DIFFICULTY = 20

BLOCK_TIME_IN_SECONDS = 5

BLOCK_REWARD = 10

class Transaction:
    def __init__(self):
        pass
    
    def __str__(self):
        return jsonpickle.encode(self)
    
    def compute_hash(self):
        pass
    
class Block:
    def __init__(self):
        pass

    def __str__(self):        
        return jsonpickle.encode(self)
    
    def compute_hash(self):        
        pass
    
    def difficulty_to_target(self):        
        return format((2**256 - 1) >> self.difficulty, '064x')        

class Blockchain:    

    def __init__(self):
        pass
    
    def create_genesis_block(self):
        pass

    def get_blockchain_size(self):
        return len(self.blocks)
    
    def get_last_block(self):
        return self.blocks[-1]
    
    def add_block(self, block):                  
        pass
    
    def compute_next_difficulty(self):        
        if len(self.blocks) > 1:            
            block_time_diff = self.get_last_block().timestamp - self.blocks[-2].timestamp                            
            if block_time_diff < BLOCK_TIME_IN_SECONDS:
                return self.get_last_block().difficulty + 1
            else:
                return self.get_last_block().difficulty - 1
        else:
            return START_DIFFICULTY
    
    def load_from(self, chain_dump):	
        self.blocks = []

        for block_data in chain_dump:	
            block = Block(height=block_data['height'],	
                        difficulty=block_data['difficulty'],	
                        previous_hash=block_data['previous_hash'],	
                        transactions=block_data['transactions'],	
                        timestamp=block_data['timestamp'])	
            block.nonce = block_data['nonce']	

            added = self.add_block(block)        	
            if not added:	
                logger.error('Load failed!')	
                return False	
            logger.info('Block %d processed successfuly!' % block.height)	

        logger.info('Loaded successfuly!')	
        return True
