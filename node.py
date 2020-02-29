# node.py defines a node in network. It contains the general operation of a node in a blockchain

from blockchain import Block, Blockchain, Transaction
import requests
import json
import time
import logging
import Crypto
from Crypto.PublicKey import RSA
from Crypto import Random
import base64

# get logger to print stuff
logger = logging.getLogger()

# key size in bits, 2048 is strong and standard!
KEY_LENGTH = 2048

# 10 coins will be awarded to the miner who solves a block! (finds its nonce)
BLOCK_REWARD = 10

# the Node class defines a Node and it's operation
class Node:
    # constructor
    def __init__(self):
        # init the transaction pool (unmined transactions)
        self.transaction_pool = []
        # create our blockchain!
        self.blockchain = Blockchain()        
        # this flag is used to signal the miner if a new block is received from the network
        # it moves forward to the next block, discarding the current minining operation
        self.new_block_received = False        
        # generate a key for this node. this key is this node's identity and is used to sign transactions
        # on behalf of this node.
        self.private_key = RSA.generate(KEY_LENGTH, Random.new().read)        
        logger.info('Address generated for node: %s' % self.address())
    
    # address returns the address for this node
    # for simplicity we define address as the public key of this node
    def address(self):
        # we use a DER dump of the public key to calculate the address. DER is basically a binary dump of the public key.
        return base64.b64encode(self.private_key.publickey().exportKey('DER')).decode()
    
    # find_nonce receives a block and tries nonces until the block hash is smaller than our target (which is
    # calculated based on difficulty). This actually 'solves' a block!
    def find_nonce(self, block):
        # start from zero
        block.nonce = 0
        # calculate the block hash
        current_hash = block.compute_hash()        
        # try until we find a nonce which solves the block
        while not current_hash < block.difficulty_to_target():
            # break from mining of a new block is received while we're mining
            if self.new_block_received:                
                break
            # try the next nonce
            block.nonce += 1
            # update the timestamp
            block.timestamp = time.time()            
            # calculate the hash again with new nonce
            current_hash = block.compute_hash()        

    # mine_block mines one block
    def mine_block(self):        
        # if no blocks, create the genesis block
        if len(self.blockchain.blocks) == 0:
            self.blockchain.create_genesis_block()
            logger.info('Genesis block created!') 
        else:
            # calculate what the next diffculty should be
            new_block_difficulty = self.blockchain.compute_next_difficulty()        

            # add all transactions from the transaction pool to this block
            tx_list = []
            for tx in self.transaction_pool:
                tx_list.append(tx)

            # create the block
            block_candidate = Block()            
            # set the new blocks fields based on current blockchain
            block_candidate.fill_block(                
                height=self.blockchain.get_last_block().height + 1, 
                difficulty=new_block_difficulty,
                previous_hash=self.blockchain.get_last_block().hash, 
                transactions=tx_list, 
                timestamp=time.time())
            
            # create the coinbase transaction, awards BLOCK_REWARD coins to ourselves (the miner)
            coinbase_tx = Transaction(                    
                from_pubkey='COINBASE',
                to_pubkey=self.address(),
                amount=BLOCK_REWARD)               
            # sign the coinbase transaction
            self.sign_transaction(coinbase_tx)
            # add it to the list of transactions for this block
            block_candidate.transactions.append(coinbase_tx)

            logger.info('Mining block %d ... [difficulty=%d] [target=%s]' %
                (block_candidate.height, block_candidate.difficulty, block_candidate.difficulty_to_target()))

            # find the correct nonce for this block, this takes a while to calculate, hopefully BLOCK_TIME_IN_SECONDS
            self.find_nonce(block_candidate)

            # if find_nonce terminated because we received a new block discard the block
            if self.new_block_received:
                logger.info('Skipped block %d' % block_candidate.height)            
                # reset the flag
                self.new_block_received = False
                # well, we did not mine anything
                return False
            else:                            
                # try adding the block to our current blockchain using add_block
                if not self.blockchain.add_block(block_candidate):            
                    # add_block failed! something was not right in the new block
                    logger.error('Mined block %d discarded!' % block_candidate.height)
                    return False
                else:
                    # clear the transaction pool. Those transactions are now safely in a block in the blockchain
                    self.transaction_pool = []
                    logger.info('Block %d mined!' % block_candidate.height)            
                    # mining successful!
                    return True
    
    # new_transaction creates a new transaction and adds it to the transaction pool
    def new_transaction(self, transaction):                        
        # check if we have enough coins to execute that transaction
        if not self.address() in self.blockchain.balances or self.blockchain.balances[self.address()] < transaction['amount']:
            logger.error('You dont have %d!' % transaction['amount'])
            return False
        # create the transaction object
        tx = Transaction(
            from_pubkey=self.address(),
            to_pubkey=transaction['to'],
            amount=transaction['amount'])
        # sign it with our private key
        self.sign_transaction(tx)        
        # add it to the transaction pool, waiting to be mined in a block
        self.transaction_pool.append(tx)
        logger.info('Transaction %d to %s added to transaction pool!' % (transaction['amount'], transaction['to']))
        # done!
        return True
    
    # sync_with_dump gets a full blockchain dump and recreates it as an object
    def sync_with_dump(self, blockchain_dump):        
        logger.info("Syncing ... dump size: %d current size: %d" %(len(blockchain_dump), self.blockchain.get_blockchain_size()))
        # new blockchain should be longer than our own
        if len(blockchain_dump) > self.blockchain.get_blockchain_size():
            # create the Blockchain
            new_blockchain = Blockchain()            
            # use load_from to load the blockchain
            if new_blockchain.load_from(blockchain_dump):                
                # load_from was successful, set the nodes blockchain to the new one just parsed
                self.blockchain = new_blockchain
                # restart the miner if running
                self.new_block_received = True
        else:
            logger.info('Did not sync!')
    
    # sign_transaction signs a transaction using the nodes private key
    def sign_transaction(self, tx):                
        # RSA sign
        tx.signature = self.private_key.sign(tx.compute_hash().encode(),'')[0]   

