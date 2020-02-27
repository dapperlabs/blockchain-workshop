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

mining = False

@app.route('/start_mining', methods=['GET'])
def start_mining():    
    global mining

    if mining:
        return 'Already mining!', 400
    else:
        
        mining = True  
        
        miner_thread = threading.Thread(target=miner)
        miner_thread.start()
        
        return 'Success'

@app.route('/stop_mining', methods=['GET'])
def stop_mining():    
    global mining

    if not mining:
        return 'Already not mining!', 400
    else:
        logger.info('Stopping miner ...')        
        mining = False        
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
    
    if node.new_transaction(req_data):
        return 'Success', 201
    else:
        return 'Failed', 400

@app.route('/balances', methods=['GET'])
def balances():    
    return json.dumps(node.blockchain.balances)    

@app.route('/tx_pool', methods=['GET'])
def get_tx_pool():
    transactions = []
    for tx in node.transaction_pool:
        transactions.append(str(tx))    
    return json.dumps(transactions)    

@app.route('/greet', methods=['POST'])
def greet():    
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
    logger.info('Running consensus ...') 
    longest_chain = None
    current_size = node.blockchain.get_blockchain_size()

    data = {'address': request.host_url}
    headers = {'Content-Type': 'application/json'}

    for peer_address in peers:    
        try:
            response = requests.post(peer_address + '/greet',
                                data=json.dumps(data), headers=headers)
        except requests.ConnectionError:
            logger.error('Could not connect to %s!' % peer_address)
            continue

        if response.status_code == 200:        
            new_peers = response.json()['peers']
            for peer in new_peers:
                if not peer.startswith(request.host_url):
                    add_peer(peer)

            size = response.json()['chain_size']
            if size > current_size:
                longest_chain = response.json()['blocks']            
                current_size = size            
            
        else:        
            logger.error('Invalid response received %d' % response.status_code)
    
    if longest_chain:
        node.sync_with_dump(longest_chain)
    
    return 'Done', 200

@app.route('/new_block_mined', methods=['POST'])
def new_block_mined():
    block_json = request.get_json()
    received_block = Block()
    if received_block.load_from(block_json):
        if node.blockchain.add_block(received_block):
            logger.info('Block %d accepted from the network!' % received_block.height)
            node.new_block_received = True
            for peer_address in peers:        
                if not request.remote_addr in peer_address:
                    try:
                        url = peer_address + '/new_block_mined'
                        requests.post(url, data=request.data, headers=request.headers)    
                        logger.info('Forwarded to %s' % peer_address)    
                    except requests.ConnectionError:
                        logger.info('Could not connect to %s!' % peer_address)            
            return 'Accepted', 201
        else:            
            return 'Rejected', 400    
    else:
        logger.info('Block %d rejected by load_from!' % received_block.height)
        return 'Rejected', 400 
    
def announce_new_block(block):    
    current_chain_size = node.blockchain.get_blockchain_size()
    consensus()
    if current_chain_size != node.blockchain.get_blockchain_size():
        logger.info('Mined block %d not announced!' % block.height)
        return

    logger.info('Announcing block %d to %d peers ...' % (block.height, len(peers)))

    data = str(block)
    headers = {'Content-Type': 'application/json'}
    
    for peer_address in peers:        
        try:
            url = peer_address + '/new_block_mined'
            requests.post(url, data=data, headers=headers)    
            logger.info('Announced to %s' % peer_address)    
        except requests.ConnectionError:
            logger.info('Could not connect to %s!' % peer_address)            
        

def miner():    
    while mining:
        if node.mine_block():
            announce_new_block(node.blockchain.get_last_block())
        node.new_block_received = False
    logger.info('Miner stopped.')

def add_peer(peer_address):
    if peer_address.endswith('/'):
        peer_address = peer_address[:-1]

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
