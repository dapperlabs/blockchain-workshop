from flask import Flask, request
import requests
import json
import logging
import sys
import threading
import signal
from logging.config import dictConfig

from node import Node
from blockchain import Block

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s - %(levelname)s] %(message)s',
    }},
    'handlers': {'console': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
})

app =  Flask('app')

node = Node()

peers = []

logger = logging.getLogger()

@app.route('/start_mining', methods=['GET'])
def start_mining():    
    if node.mining:
        return 'Already mining!', 400
    else:
        miner_thread = threading.Thread(target=node.mine)
        miner_thread.start()
        return 'Success'

@app.route('/stop_mining', methods=['GET'])
def stop_mining():    
    if not node.mining:
        return 'Already not mining!', 400
    else:
        node.stop_mining()
        return 'Success'

@app.route('/info', methods=['GET'])
def get_info():    
    blocks = []
    for block in node.blockchain.blocks:
        blocks.append(str(block))
    return json.dumps({'chain_size': node.blockchain.get_blockchain_size(),                       
                       'peers': peers,
                       'blocks': blocks})

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    req_data = request.get_json()
    required_fields = ['to', 'amount']

    for field in required_fields:
        if not req_data.get(field):
            return 'Invalid request: missing field %s' % field, 400    
    
    node.new_transaction(req_data)

    return 'Success', 201

# @app.route('/mine', methods=['GET'])
# def mine_transaction_pool():
#     result = node.mine()
#     if not result:
#         return 'Transaction pool is empty'
#     else:
#         chain_length = len(node.blockchain)
#         node.consensus()
#         if chain_length == len(node.blockchain.chain):            
#             node.announce_new_block(node.blockchain.get_last_block)
#         return 'Block #{} is mined.'.format(node.blockchain.get_last_block.index)    

@app.route('/tx_pool', methods=['GET'])
def get_tx_pool():
    transactions = []
    for tx in node.transaction_pool:
        transactions.append(tx.__dict__)
    # return json.dumps({'blockchain': blockchain})
    return json.dumps(transactions)    

@app.route('/hello', methods=['POST'])
def hello():    
    peer_address = request.get_json()['address']
    if not peer_address:
        return 'Missing address', 400

    add_peer(peer_address)

    return get_info()

@app.route('/add_peer', methods=['POST'])
def add_peer_and_consensus():    
    peer_address = request.get_json()['address']
    if not peer_address:
        return 'Missing address', 400
    
    add_peer(peer_address)

    return consensus()    

@app.route('/consensus', methods=['GET'])
def consensus():    
    longest_chain = None
    current_size = node.blockchain.get_blockchain_size()

    data = {'address': request.host_url}
    headers = {'Content-Type': 'application/json'}

    for peer_address in peers:    
        response = requests.post(peer_address + '/hello',
                                data=json.dumps(data), headers=headers)

        if response.status_code == 200:        
            new_peers = response.json()['peers']
            for peer in new_peers:
                add_peer(peer)

            size = response.json()['chain_size']
            if size > current_size:
                longest_chain = response.json()['blocks']            
                current_size = size            
            
        else:        
            peers.remove(peer)
    
    if longest_chain:
        node.sync_with_dump(longest_chain)
    
    return 'Done', 200

@app.route('/new_block_mined', methods=['POST'])
def new_block_mined():
    block_fields = request.get_json()
    block = Block(block_fields['height'],
                    block_fields['previous_hash'],
                    block_fields['transactions'])
    
    added = node.blockchain.add_block(block)

    if not added:
        return 'The block was not added', 400

    return 'Block added', 201

def add_peer(peer_address):
    if peer_address not in peers:
        logger.info("New peer added: %s", peer_address)
        peers.append(peer_address)
    else:
        logger.info("Peer already registered: %s", peer_address)        

if len(sys.argv) != 2:
    print('Usage: python app.py PORT_NUMBER')
    raise SystemExit

# def handle_killsig(signum,frame):    
#     print('\nGoodbye!')
#     node.kill()
#     raise SystemExit
# signal.signal(signal.SIGINT,handle_killsig) 

app.run(debug=True, port=sys.argv[1], use_reloader=False)
