from blockchain import Block, Blockchain, from_dump
import requests
import json
import time


class Node:
    def __init__(self):
        self.transaction_pool = []
        self.blockchain = Blockchain()    
        self.peers = set()    
    
    def new_transaction(self, transaction):
        self.transaction_pool.append(transaction)
    
    def add_peer(self, peer_address):
        self.peers.add(peer_address)
    
    def update_peers(self, peers):
        self.peers.update(peers)

    def mine(self):                
        new_block_difficulty = self.blockchain.compute_next_difficulty()        
        
        print('Mining difficulty=%d ...' % new_block_difficulty)
        
        new_block = Block(
            height=self.blockchain.get_last_block().height + 1, 
            difficulty=new_block_difficulty,
            previous_hash=self.blockchain.get_last_block().hash, 
            transactions=self.transaction_pool, 
            timestamp=time.time())

        self.find_nonce(new_block)

        if not self.blockchain.add_block(new_block):            
            return False

        self.transaction_pool = []

        # todo, needed?
        return new_block.height

    def find_nonce(self, block):
        block.nonce = 0
        current_hash = block.compute_hash()
        print( block.difficulty_to_target())
        while not current_hash < block.difficulty_to_target():
            block.nonce += 1
            block.timestamp = time.time()
            current_hash = block.compute_hash()        
    
    def sync_with_dump(self, blockchain_dump):
        self.blockchain = from_dump(blockchain_dump)
    
    def consensus(self):
        longest_chain = None
        current_len = len(self.blockchain)

        for peer_address in self.peers:
            response = requests.get('{}/chain'.format(peer_address))
            length = response.json()['length']                        
            if length > current_len:
                blockchain = from_dump(response.json()['blockchain'])
                if blockchain:
                    # Longer valid chain found!
                    current_len = length
                    longest_chain = blockchain

        if longest_chain:
            self.blockchain = longest_chain
            return True

        return False
    
    def announce_new_block(self, block):    
        for peer_address in self.peers:
            url = '{}/new_block_mined'.format(peer_address)
            requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))
    
    def run(self):      
        self.alive = True  
        while self.alive:
            self.mine()
            print('Block %d mined!' % self.blockchain.get_last_block().height) 
            # print(self.blockchain)
    
    def kill(self):
        self.alive = False
