# blockchain.py provides basic blockchain objects for our node
# specifically, it provides Transaction, Block and Blockchain objects

from hashlib import sha256
import json
import time
import logging
from Crypto.PublicKey import RSA
import base64

# get logger to print out stuff
logger = logging.getLogger()

# this is the start difficulty for our blockchain
START_DIFFICULTY = 10

# we target 5 seconds interval between blocks. Our blockchain increases difficulty (makes mining more difficult)
# if two blocks are mined in less than 5 seconds apart, and decreases difficulty (makes mining easier) if blocks
# are generated in more than 5 seconds apart
BLOCK_TIME_IN_SECONDS = 5

# 10 coins will be awarded to the miner who solves a block! (finds its nonce)
BLOCK_REWARD = 10

# the Transaction cass defines a transaction
class Transaction:
    # each transaction has 'from', 'to' and 'amount'
    # keep in mind addresses ('from' and 'to') are public keys of nodes
    def __init__(self, from_pubkey, to_pubkey, amount):
        self.from_pubkey = from_pubkey
        self.to_pubkey = to_pubkey
        self.amount = amount    
        # blank signature when creating a transaction
        self.signature = ''        
    
    # returns a string representation of this class
    def __str__(self):
        # use JSON dump on all 4 fields
        return json.dumps({
            'from': self.from_pubkey,
            'to': self.to_pubkey,
            'amount': self.amount,
            'signature': self.signature})
    
    # returns a hash for this Transaction object
    def compute_hash(self):          
        # exclude signature, as we sign the tx hash
        tx_str = json.dumps({
            'from': self.from_pubkey,
            'to': self.to_pubkey,
            'amount': self.amount})
        # use sha256 for hashing, return a hexdigest string
        return sha256(tx_str.encode()).hexdigest()
    
    # verify_signature verifies the transaction signature
    # its worth mentioning that you don't need to be owner (from) of this transaction
    # to be able to verify it's signature.
    def verify_signature(self):        
        # use the public key from 'from' field
        signer = self.from_pubkey
        # COINBASE transactions are different, pick 'to' field as signer
        if self.from_pubkey == 'COINBASE':
            signer = self.to_pubkey
        
        # load the key from the signer field
        key = RSA.importKey(base64.b64decode(signer))        
        # verify transaction using RSA
        return key.verify(self.compute_hash().encode(), [self.signature])
    
# the Block class defines a block which is a grouping of transactions chained to other blocks using hashes
class Block:
    # empty constructor
    def __init__(self):        
        # height is the index of the block in blockchain
        self.height = -1
        # difficulty defines how hard it is to create this block.
        # this value is captured per block, as difficulty changes through time
        # when new nodes join a blockchain it should be more difficult to mine
        # because we want two blocks to be BLOCK_TIME_IN_SECONDS seconds apart
        self.difficulty = 0
        # chains this block to the last one
        # keep in mind previous_hash is part of block hash!
        self.previous_hash = ''        
        self.transactions = []
        self.timestamp = time.time()
        self.nonce = 0

    # fill_block fills the block with provided values
    def fill_block(self, height, difficulty, previous_hash, transactions, timestamp):
        self.height = height        
        self.difficulty = difficulty
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp
        # set nonce to zero. we have to find the correct value in mining        
        self.nonce = 0

    # returns a string representation of this Block
    def __str__(self):        
        # stringify all the transactions in this block
        tx_dump = [str(tx) for tx in self.transactions]
        
        # use JSON as stringify function
        return json.dumps({
            'height': self.height,
            'difficulty': self.difficulty,
            'nonce': self.nonce,
            'previous_hash': self.previous_hash,
            'transactions': tx_dump,
            'timestamp': self.timestamp})        
    
    # compute_hash computes hash of this block. Hashes are fingerprints of data!
    def compute_hash(self):        
        # hash all the transactions in a block and put them in a list
        tx_hashes = [tx.compute_hash() for tx in self.transactions]
        
        # JSON representation of block and hash of all its transactions
        block = json.dumps({
            'height': self.height,
            'difficulty': self.difficulty,
            'nonce': self.nonce,
            'previous_hash': self.previous_hash,
            'transactions': ','.join(tx_hashes),
            'timestamp': self.timestamp})
        # hash all the block data and transactions defined aboves
        return sha256(block.encode()).hexdigest()
    
    # difficulty_to_target converts difficulty to target. Target is the value that 
    # defines what the maximum value for an acceptable hash is based on difficulty
    # if difficulty increases, target decreases and vice versa    
    def difficulty_to_target(self):        
        # (2**256 - 1) is 'fff...f' (256 bits)
        # shifting this value right creates zeroes on the left side ('difficulty' number of times!)
        return format((2**256 - 1) >> self.difficulty, '064x')        
    
    # load_from accpets a JSON dump of a block and recreates it as an object
    def load_from(self, block_data):        
        # contains transaction list for this block
        tx_list = []            
        # process transactions
        for tx in block_data['transactions']:                
            # create transaction
            tx_data = json.loads(tx)
            tx = Transaction(
                from_pubkey=tx_data['from'],
                to_pubkey=tx_data['to'],
                amount=tx_data['amount'],
            )
            tx.signature = tx_data['signature']            
            # add it to the transaction list defined above
            tx_list.append(tx)            
        
        # set block properties
        self.height = block_data['height']
        self.difficulty = block_data['difficulty']
        self.previous_hash = block_data['previous_hash']
        self.transactions = tx_list
        self.timestamp = block_data['timestamp']
        self.nonce = block_data['nonce']	        
        
        # we've processed successfully!
        return True

# the Blockchain class defines a blockchain as an object
class Blockchain:    

    # constructor
    def __init__(self):
        # our blockchain has only two properties: a list of blocks and a set of balances for public keys        
        self.blocks = []
        # its worth mentioning that list of balances is calculated based on list of blocks!
        self.balances = {}
    
    # create_genesis_block creates the first blockchain block! this is a special block as there is none before
    def create_genesis_block(self):
        genesis_block = Block()
        genesis_block.fill_block(
            height=1, 
            difficulty=START_DIFFICULTY,
            previous_hash='0',
            transactions=[],
            timestamp=time.time())    
        # add it to the blockchain
        self.add_block(genesis_block)

    # get_blockchain_size calculates the size of blockchain
    def get_blockchain_size(self):
        return len(self.blocks)
    
    # get_last_block returns the last block
    def get_last_block(self):
        return self.blocks[-1]
    
    # add_block adds a block to our blockchain. This function checks everything to make sure
    # the added block is correct and sound
    def add_block(self, block):                  
        # set the blocks hash
        block.hash = block.compute_hash()        
        
        # these checks are for non-genesis blocks
        if block.height > 1:  
            # check height
            if block.height != self.get_last_block().height + 1:
                logger.error('Block %d is invalid: expected height is %d' % (block.height, self.get_last_block().height + 1))
                return False

            # checks previous_hash 
            if block.previous_hash != self.get_last_block().hash:                                                
                logger.error('Block %d is invalid: block.previous_hash is %s should be %s' % (block.height, block.previous_hash, self.get_last_block().hash))
                return False

            # check nonce
            if not block.hash < block.difficulty_to_target():                
                logger.error('Block %d is invalid: block.hash is %s should be smaller than %s' % (block.height, block.hash, block.difficulty_to_target()))
                return False        

            # check difficulty
            if block.difficulty != self.compute_next_difficulty():
                logger.error('Block %d is invalid: block.difficulty is %d should be %d' % (block.height, block.difficulty, self.compute_next_difficulty()))
                return False

        # now we check each transaction in this block
        coinbase_found = False                
        for tx in block.transactions:

            # verify transaction signature
            if not tx.verify_signature():
                logger.error('Block %d is invalid: invalid signature!' % block.height)
                return False

            # coinbase transaction logic
            if tx.from_pubkey == 'COINBASE':
                # each block should have only 1 coinbase transaction!
                if coinbase_found:
                    logger.error('Block %d is invalid: more than 1 COINBASE' % block.height)                    
                    return False
                # check reward amount
                if tx.amount != BLOCK_REWARD:
                    logger.error('Block %d is invalid: invalid COINBASE amount %d' % (block.height, tx.amount))
                    return False
                # flag we've found the coinbase transaction
                # we use this flag to check there is only 1 coinbase
                coinbase_found = True                
            else:
                # check if the 'from' public key has enough coins to give 
                if not tx.from_pubkey in self.balances or self.balances[tx.from_pubkey] < tx.amount:
                    logger.error('Block %d is invalid: insufficient funds %d address %s' % (block.height, tx.amount, tx.from_pubkey))
                    return False
                else:                    
                    # update balance to account for spent coins
                    self.balances[tx.from_pubkey] -= tx.amount                    
            
            # add the amount to receipient
            if tx.to_pubkey in self.balances:
                self.balances[tx.to_pubkey] += tx.amount
            else:
                self.balances[tx.to_pubkey] = tx.amount

        # all ok! add the block to the blockchain
        self.blocks.append(block)        
        
        # success!
        return True
    
    # compute_next_difficulty calculates the difficulty for next block. It checks the time it took to 
    # create the last two blocks and compares it to BLOCK_TIME_IN_SECONDS and acts accordingly
    def compute_next_difficulty(self):        
        # if we have more than 1 block
        if len(self.blocks) > 1:            
            # calculate the time difference between last 2 blocks
            block_time_diff = self.get_last_block().timestamp - self.blocks[-2].timestamp                            
            # tweak difficulty based on time
            if block_time_diff < BLOCK_TIME_IN_SECONDS:
                # increase difficulty if the last two blocks are mined fast
                return self.get_last_block().difficulty + 1
            else:
                # decrease difficulty if the last two blocks are mined slow
                return self.get_last_block().difficulty - 1
        else:
            # block 1 is mined with START_DIFFICULTY
            return START_DIFFICULTY
    
    # load_from accpets a JSON dump of a blockchain and recreates it as an object in self
    def load_from(self, json_dump):	
        # init an empty list of blocks
        self.blocks = []

        # for each block in dump
        for block_data_json in json_dump:	
            # create the block
            block = Block()
            # fill it with data we received
            block_data = json.loads(block_data_json)
            if block.load_from(block_data):                
                # call add_block to add this block to the blockchain, checking everything!
                if self.add_block(block):	
                    logger.info('Block %d processed successfully!' % block.height)	                    
                else:
                    # add_block failed! return False as error
                    logger.error('Load failed!')	
                    return False	

        # success!
        logger.info('Loaded successfully!')	
        return True
