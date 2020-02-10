from blockchain import Block, Blockchain

class Node:
    def __init__(self):
        self.transaction_pool = []
        self.blockchain = Blockchain()        
    
    def new_transaction(self, transaction):
        self.transaction_pool.append(transaction)

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

    def find_nonce(self, block, difficulty):
        block.nonce = 0
        current_hash = block.compute_hash()
        while not current_hash.startswith('0' * difficulty):
            block.nonce += 1
            current_hash = block.compute_hash()        
    
