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
        self.new_block_received = False        
        self.private_key = RSA.generate(KEY_LENGTH, Random.new().read)        
        logger.info('Address generated for node: %s' % self.address())
    
    def address(self):
        return base64.b64encode(self.private_key.publickey().exportKey('DER')).decode()
    
    def find_nonce(self, block):
        block.nonce = 0
        current_hash = block.compute_hash()        
        while not current_hash < block.difficulty_to_target():
            if self.new_block_received:                
                break
            block.nonce += 1
            block.timestamp = time.time()            
            current_hash = block.compute_hash()        

    def mine_block(self):        
        if len(self.blockchain.blocks) == 0:
            self.blockchain.create_genesis_block()
            logger.info('Genesis block created!') 
        else:
            new_block_difficulty = self.blockchain.compute_next_difficulty()        

            tx_list = []
            for tx in self.transaction_pool:
                tx_list.append(tx)

            block_candidate = Block()            
            block_candidate.fill_block(
                height=self.blockchain.get_last_block().height + 1, 
                difficulty=new_block_difficulty,
                previous_hash=self.blockchain.get_last_block().hash, 
                transactions=tx_list, 
                timestamp=time.time())
            
            coinbase_tx = Transaction(                    
                from_pubkey='COINBASE',
                to_pubkey=self.address(),
                amount=BLOCK_REWARD)               
            self.sign_transaction(coinbase_tx)
            block_candidate.transactions.append(coinbase_tx)

            logger.info('Mining block %d ... [difficulty=%d] [target=%s]' %
                (block_candidate.height, block_candidate.difficulty, block_candidate.difficulty_to_target()))

            self.find_nonce(block_candidate)

            if self.new_block_received:
                logger.info('Skipped block %d' % block_candidate.height)            
                self.new_block_received = False
                return False
            else:                            
                if not self.blockchain.add_block(block_candidate):            
                    logger.error('Mined block %d discarded!' % block_candidate.height)
                    return False
                else:
                    self.transaction_pool = []
                    logger.info('Block %d mined!' % block_candidate.height)            
                    return True
    
    def new_transaction(self, transaction):
        # todo: check tx validity (balance)
        tx = Transaction(
            from_pubkey=self.address(),
            to_pubkey=transaction['to'],
            amount=transaction['amount'])
        self.sign_transaction(tx)        
        self.transaction_pool.append(tx)
    
    def sync_with_dump(self, blockchain_dump):        
        logger.info("Syncing ... dump size: %d current size: %d" %(len(blockchain_dump), self.blockchain.get_blockchain_size()))
        if len(blockchain_dump) > self.blockchain.get_blockchain_size():
            new_blockchain = Blockchain()            
            if new_blockchain.load_from(blockchain_dump):                
                self.blockchain = new_blockchain
                self.new_block_received = True
        else:
            logger.info('Did not sync!')
    
    def sign_transaction(self, tx):                
        tx.signature = self.private_key.sign(tx.compute_hash().encode(),'')[0]
    

