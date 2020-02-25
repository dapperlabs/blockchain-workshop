from blockchain import Block, Blockchain, Transaction
import requests
import json
import time
import logging
import Crypto
from Crypto.PublicKey import RSA
from Crypto import Random
import base64

logger = logging.getLogger()

KEY_LENGTH = 2048

BLOCK_REWARD = 10

class Node:
    def __init__(self):
        self.transaction_pool = []
        self.blockchain = Blockchain()        
        self.mining = False        
        self.private_key = RSA.generate(KEY_LENGTH, Random.new().read)        
        logger.info('Address generated! %s' % self.address())
    
    def address(self):
        return str(self.private_key.publickey().exportKey('PEM'))
    
    def find_nonce(self, block):
        block.nonce = 0
        current_hash = block.compute_hash()        
        while not current_hash < block.difficulty_to_target():
            block.nonce += 1
            block.timestamp = time.time()            
            current_hash = block.compute_hash()       
        print('MINED ' + str(block))

    def mine(self):      
        self.mining = True  
        while self.mining:
            if len(self.blockchain.blocks) == 0:
                self.blockchain.create_genesis_block()
                logger.info('Genesis block created!') 
            else:
                new_block_difficulty = self.blockchain.compute_next_difficulty()        
            
                logger.info('[difficulty=%d] Mining block %d ...' % (new_block_difficulty, self.blockchain.get_last_block().height + 1))
                
                coinbase_tx = Transaction(                    
                    from_pubkey='COINBASE',
                    to_pubkey=self.address(),
                    amount=BLOCK_REWARD)                
                self.transaction_pool.append(coinbase_tx)

                new_block = Block(
                    height=self.blockchain.get_last_block().height + 1, 
                    difficulty=new_block_difficulty,
                    previous_hash=self.blockchain.get_last_block().hash, 
                    transactions=self.transaction_pool, 
                    timestamp=time.time())

                self.find_nonce(new_block)

                if not self.blockchain.add_block(new_block):            
                    logger.error('Mined block %d discarded!' % self.blockchain.get_last_block().height) 
                else:
                    self.transaction_pool = []
                    logger.info('Block %d mined!' % self.blockchain.get_last_block().height)
        
        logger.info('Miner stopped.')
    
    def stop_mining(self):
        logger.info('Stopping miner ...')        
        self.mining = False
    
    def new_transaction(self, transaction):
        # todo: check tx validity (balance)
        tx = Transaction(
            from_pubkey=self.address(),
            to_pubkey=transaction['to'],
            amount=transaction['amount'])
        tx.signature = str(self.private_key.sign(tx.compute_hash().encode(),'')[0])
        self.transaction_pool.append(tx)
    
    def sync_with_dump(self, blockchain_dump):        
        logger.info("Syncing ... dump size: %d current size: %d" %(len(blockchain_dump), self.blockchain.get_blockchain_size()))
        if len(blockchain_dump) > self.blockchain.get_blockchain_size():
            new_blockchain = Blockchain()
            # new_blockchain.blocks = blockchain_dump            
            if new_blockchain.load_from(blockchain_dump):                
                self.blockchain = new_blockchain             
        else:
            logger.info('Did not sync!')
    
    
    
    # todo
    # def announce_new_block(self, block):    
    #     for peer_address in self.peers:
    #         url = '{}/new_block_mined'.format(peer_address)
    #         requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))    

