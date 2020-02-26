from hashlib import sha256
import json
import time
import logging
from Crypto.PublicKey import RSA
import base64

logger = logging.getLogger()

START_DIFFICULTY = 10

BLOCK_TIME_IN_SECONDS = 5

BLOCK_REWARD = 10

class Transaction:
    def __init__(self, from_pubkey, to_pubkey, amount):
        self.from_pubkey = from_pubkey
        self.to_pubkey = to_pubkey
        self.amount = amount    
        self.signature = ''        
    
    def __str__(self):
        return json.dumps({
            'from': self.from_pubkey,
            'to': self.to_pubkey,
            'amount': self.amount,
            'signature': self.signature})
    
    def compute_hash(self):  
        tx_str = json.dumps({
            'from': self.from_pubkey,
            'to': self.to_pubkey,
            'amount': self.amount})
        return sha256(tx_str.encode()).hexdigest()
    
    def verify_signature(self):        
        pub_key = self.from_pubkey
        if self.from_pubkey == 'COINBASE':
            pub_key = self.to_pubkey
        
        key = RSA.importKey(base64.b64decode(pub_key))
        # print(base64.b64encode(key.exportKey('DER')).decode())
        print(key.verify(self.compute_hash(), self.signature))
    
class Block:
    def __init__(self, height, difficulty, previous_hash, transactions, timestamp):
        self.height = height        
        self.difficulty = difficulty
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp
        self.nonce = 0

    def __str__(self):        
        tx_dump = [str(tx) for tx in self.transactions]
        
        return json.dumps({
            'height': self.height,
            'difficulty': self.difficulty,
            'nonce': self.nonce,
            'previous_hash': self.previous_hash,
            'transactions': tx_dump,
            'timestamp': self.timestamp})        
    
    def compute_hash(self):        
        tx_hashes = [tx.compute_hash() for tx in self.transactions]
        
        block = json.dumps({
            'height': self.height,
            'difficulty': self.difficulty,
            'nonce': self.nonce,
            'previous_hash': self.previous_hash,
            'transactions': ','.join(tx_hashes),
            'timestamp': self.timestamp})
        return sha256(block.encode()).hexdigest()
    
    def difficulty_to_target(self):        
        return format((2**256 - 1) >> self.difficulty, '064x')        

class Blockchain:    

    def __init__(self):
        self.blocks = []
        self.balances = {}
    
    def create_genesis_block(self):
        genesis_block = Block(
            height=1, 
            difficulty=START_DIFFICULTY,
            previous_hash='0',
            transactions=[],
            timestamp=time.time())    
        self.add_block(genesis_block)

    def get_blockchain_size(self):
        return len(self.blocks)
    
    def get_last_block(self):
        return self.blocks[-1]
    
    def add_block(self, block):                  
        block.hash = block.compute_hash()        
        
        if block.height > 1:            
            if block.difficulty != self.compute_next_difficulty():
                logger.error('Block %d is invalid: block.difficulty is %d should be %d' % (block.height, block.difficulty, self.compute_next_difficulty()))
                return False

            if block.previous_hash != self.get_last_block().hash:                                                
                logger.error('Block %d is invalid: block.previous_hash is %s should be %s' % (block.height, block.previous_hash, self.get_last_block().hash))
                return False

            if not block.hash < block.difficulty_to_target():                
                logger.error('Block %d is invalid: block.hash is %s should be smaller than %s' % (block.height, block.hash, block.difficulty_to_target()))
                return False        

        coinbase_found = False        
        for tx in block.transactions:
            if tx.from_pubkey == 'COINBASE':
                if coinbase_found:
                    logger.error('Block %d is invalid: more than 1 COINBASE' % block.height)
                    return False
                if tx.amount != BLOCK_REWARD:
                    logger.error('Block %d is invalid: invalid COINBASE amount %d' % (block.height, tx.amount))
                    return False
                coinbase_found = True
            else:
                if self.balances[tx.from_pubkey] < tx.amount:
                    logger.error('Block %d is invalid: insufficient funds %d address %s' % (block.height, tx.amount, tx.from_pubkey))
                    return False
                else:
                    # todo: verify signature!
                    self.balances[tx.from_pubkey] -= tx.amount
                    self.balances[tx.to_pubkey] += tx.amount

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
    
    def load_from(self, json_dump):	
        self.blocks = []

        for block_data_json in json_dump:	
            block_data = json.loads(block_data_json)

            tx_list = []            
            for tx in block_data['transactions']:                
                tx_data = json.loads(tx)
                tx = Transaction(
                    from_pubkey=tx_data['from'],
                    to_pubkey=tx_data['to'],
                    amount=tx_data['amount'],
                )
                if tx.verify_signature():
                    tx_list.append(tx)
                else:
                    logger.error('Invalid signature! %s' % str(tx))	
                    return False	    

            block = Block(height=block_data['height'],	
                        difficulty=block_data['difficulty'],	
                        previous_hash=block_data['previous_hash'],	
                        transactions=tx_list,	
                        timestamp=block_data['timestamp'])	
            block.nonce = block_data['nonce']	

            added = self.add_block(block)        	
            if not added:	
                logger.error('Load failed!')	
                return False	
            logger.info('Block %d processed successfuly!' % block.height)	

        logger.info('Loaded successfuly!')	
        return True
