from blockchain import Block, Blockchain, from_dump
import requests
import json

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
        if not self.transaction_pool:            
            return False
        
        new_block_height = self.blockchain.get_last_block().height + 1        
        new_block_previous_hash = self.blockchain.get_last_block().hash
        new_block_transactions = self.transaction_pool
        new_block = Block(new_block_height, new_block_previous_hash, new_block_transactions)        

        self.find_nonce(new_block, self.blockchain.difficulty)

        if not self.blockchain.add_block(new_block):            
            return False

        self.transaction_pool = []

        return new_block.height

    def find_nonce(self, block, difficulty):
        block.nonce = 0
        current_hash = block.compute_hash()
        while not current_hash.startswith('0' * difficulty):
            block.nonce += 1
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