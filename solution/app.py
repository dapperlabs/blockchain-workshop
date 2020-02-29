# app.py provides the Flask application for our node.
# This file provides code for our node to interface with you and other nodes (called peers).
# We use RESTful communication with HTTP endpoints to accomplish this.

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

# configures logging to be prettier, adds datetime and level
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
logger = logging.getLogger()

# create our Flask app. Flask provides easy RESTful support for Python.
app =  Flask('app')

# create a node object. Node will provide most of our blockchain's functionality.
node = Node()

# this list stores a list of known peer addresses in the network.
# new blocks will be forwarded to all known peers
peers = []

# this flag stores the state of our miner. If miner is running this is True
mining = False

# GET /start_mining instructs a node to start mining. This will return an error if the node is already mining.
@app.route('/start_mining', methods=['GET'])
def start_mining():    
    # we need to modify a global variable
    global mining

    # handle the case that we are already mining
    if mining:
        # 200 is HTTP OK!
        return 'Already mining!', 200
    else:
        
        # set the global mining flag to True to indicate we are mining
        mining = True  
        
        # create a new thread for our miner. The miner should be run in background without interfering with
        # node operation like handling endpoints.
        miner_thread = threading.Thread(target=miner)
        miner_thread.start()
        
        # well, we're done!
        return 'Success', 200

# GET /stop_mining instructs a node to stop mining. This will return an error if the node is already stopped.
@app.route('/stop_mining', methods=['GET'])
def stop_mining():    
    # we need to modify a global variable
    global mining

    # handle the case when we want to stop a stopped miner!
    if not mining:
        return 'Already not mining!', 200
    else:        
        logger.info('Stopping miner ...')        
        # set the global flag to False. The miner checks for this flag on each mining iteration.
        mining = False        
        # tell the user we've done it
        return 'Success', 200

# GET /info gives basic information about this node. This endpoint returns the current blockchain size,
# a list of this node's peers and the full blockchain for this node. You can use this to debug your node.
# This endpoint is also used, when another peer wants to sync with this node's blockchain.
@app.route('/info', methods=['GET'])
def get_info():    
    # create a list of blocks to jsonify
    blocks = []
    # add all the blocks in our node's blockchain to this list
    for block in node.blockchain.blocks:
        blocks.append(str(block))
    # return the information this endpoint is responsible for
    return json.dumps({'chain_size': node.blockchain.get_blockchain_size(),                       
                       'peers': peers,
                       'blocks': blocks})

# POST /new_transaction creates a new transaction! You need to provide 'to' and 'amount'. It creates a new
# transaction moving coins from this node's wallet to the address specified in 'to' (which may be invalid!)
# This transaction is added to the node's transaction pool until it is mined in a block, and thus valid on our blockchain!
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    # check the request has all the fields we need
    req_data = request.get_json()
    required_fields = ['to', 'amount']
    for field in required_fields:
        if not req_data.get(field):
            return 'Invalid request: missing field %s' % field, 400        
    
    # call node's new_transaction function, which handles the transaction creation
    if node.new_transaction(req_data):
        # if True is returned, everything went smoothly!
        return 'Success', 201
    else:
        # if False is returned, something went wrong
        return 'Failed', 400

# GET /balances returns a list of all addresses along with their balances, according to this node's version of the blockchain
# balances do not include transactions not yet mined, it also has everyones balance because in a blockchain everybody knows what
# everybody else owns!
@app.route('/balances', methods=['GET'])
def balances():    
    # creating JSON in Python is pretty easy, nice!
    return json.dumps(node.blockchain.balances)    

# GET /tx_pool returns list of transactions in the transaction pool. These transactions are created but not yet mined!
# remember transactions in tx_pool are not yet executed by the blockchain. They will be final when they are mined in a block.
@app.route('/tx_pool', methods=['GET'])
def get_tx_pool():
    # create a list of transactions, add transactions in the transaction pool to this
    transactions = []
    for tx in node.transaction_pool:
        transactions.append(str(tx))    
    # JSON dump the results to the user
    return json.dumps(transactions)    

# POST /greet greets another node who wants to sync with this node. It needs 'address' field in the request
# to identify the peer. Retrurns get_info to the new node.
@app.route('/greet', methods=['POST'])
def greet():    
    # Extract peer_address from the request
    peer_address = request.get_json()['address']
    # Error if we didn't find the field
    if not peer_address:
        return 'Missing address', 400

    # calls add_peer to add this peer to our peer list
    add_peer(peer_address)

    # return our node's info
    return get_info()

# POST /add_peer adds a new peer to our node and syncs with it. This endpoint adds the peer to the node's list
# and calls consensus. Consensus checks the blockchain size on all peers (including the new one) and syncs with the 
# longest chain.
@app.route('/add_peer', methods=['POST'])
def add_peer_and_consensus():    
    # Extract peer_address from the request
    peer_address = request.get_json()['address']
    if not peer_address:
        return 'Missing address', 400
    
    # Adds peer to our peer list
    add_peer(peer_address)

    # Call consensus to sync with this node (or the node with the longest chain in our peer list)
    return consensus()    

# GET /consensus calls /greet on all known peers to find out about their blockchain and its size. 
# It then syncs with the node with the longest blockchain.
@app.route('/consensus', methods=['GET'])
def consensus():   
    logger.info('Running consensus ...') 
    longest_chain = None
    # current blockchain size on this node
    current_size = node.blockchain.get_blockchain_size()

    # these fields are repeated for all requests to peers
    data = {'address': request.host_url}
    headers = {'Content-Type': 'application/json'}

    # for all known peers
    for peer_address in peers:    
        try:
            # call peers /greet endpoint to find out about their blockchain
            response = requests.post(peer_address + '/greet',
                                data=json.dumps(data), headers=headers)
        except requests.ConnectionError:
            # if we can't connect to a peer, remove it from our list
            peers.remove(peer_address)
            logger.info('Could not connect to %s! Peer removed.' % peer_address)
            # go to next peer
            continue

        # if successful
        if response.status_code == 200:
            # check peers blockchain size
            size = response.json()['chain_size']
            # we're only interested in blockchains longer than our own.
            # in blockchains, size DOES matter!
            if size > current_size:
                # keep this blockchain as the longest we've encountered so far
                longest_chain = response.json()['blocks']            
                current_size = size            
            
        else:        
            logger.error('Invalid response received %d' % response.status_code)
    
    # if we found a blockchain longer than our own sync with it
    if longest_chain:
        node.sync_with_dump(longest_chain)
    
    # done!
    return 'Done', 200

# POST /new_block_mined is used to receive new blocks from the network as they are mined. This endpoint
# needs the JSON dump of the new block. An important thing to note here is the node checks the new block
# closely to make sure it is valid for our current version of the chain. If the new block is valid it's also
# propagated to our peer list so others know about this block. This is an important function to keep all nodes
# in sync with each other's version of the blockchain. 
@app.route('/new_block_mined', methods=['POST'])
def new_block_mined():
    # get the block from request
    block_json = request.get_json()
    received_block = Block()
    # load the data from the request to Block object
    if received_block.load_from(block_json):
        # this checks if this is a duplicate block we've received. assume we have 3 connected nodes
        # (A, B, C). if A mines a block and gives it to B and then B gives it to C, C doesn't know if
        # A already has this block or not. This is a quick fix for this problem, we just discard blocks
        # that we have received before! hash is a reliable way of ensuring the block is the same as the 
        # received one
        if received_block.compute_hash() == node.blockchain.get_last_block().compute_hash():
            return 'Accepted', 201
        # add_block checks the block and makes sure if can be added to our nodes blockchain
        if node.blockchain.add_block(received_block):
            logger.info('Block %d accepted from the network!' % received_block.height)
            # this flag signals the miner to move to the next block            
            node.new_block_received = True
            # propagate the new block to other known peers
            for peer_address in peers:                        
                # quick check not to send back a block to the originator
                # as a side note, this is not a reliable way to identify sender,
                # but doesn't introduce bugs as we can handle duplicate blocks (see comment a few lines above)                
                if not request.remote_addr in peer_address:
                    try:
                        # call known peers /new_block_mined
                        url = peer_address + '/new_block_mined'
                        requests.post(url, data=request.data, headers=request.headers)    
                        logger.info('Forwarded to %s' % peer_address)    
                    except requests.ConnectionError:                        
                        # could not connect to peer! remove it
                        peers.remove(peer_address)
                        logger.info('Could not connect to %s! Peer removed.' % peer_address)
            return 'Accepted', 201
        else:            
            return 'Rejected', 400    
    else:
        # could not load the block information from JSON
        logger.info('Block %d rejected by load_from!' % received_block.height)
        return 'Rejected', 400 
    
# announce_new_block is called when our node finds (mines) a new block
# it propagates that block to the network by calling /new_block_mined on
# all known peers
def announce_new_block(block):
    logger.info('Announcing block %d to %d peers ...' % (block.height, len(peers)))

    # request data and headers are the same for every known peer
    data = str(block)
    headers = {'Content-Type': 'application/json'}
    
    # for all known peers
    for peer_address in peers:        
        try:
            # call known peers /new_block_mined
            url = peer_address + '/new_block_mined'
            requests.post(url, data=data, headers=headers)    
            logger.info('Announced to %s' % peer_address)    
        except requests.ConnectionError:
            # could not connect to peer! remove it
            peers.remove(peer_address)
            logger.info('Could not connect to %s! Peer removed.' % peer_address)        

# miner indefinitely tries to mine a new block. This is controlled by /start_mining and 
# /stop_mining. A global variable called 'mining' controls whether the miner should be active or not.
def miner():    
    # as long as the miner flag is set
    while mining:
        # mine_block mines one block and returns True is successful
        if node.mine_block():
            # announce the new mined block to the network
            announce_new_block(node.blockchain.get_last_block())
        # reset the new_block_received flag when moving on to the next block
        node.new_block_received = False
    # mining flag is set to False
    logger.info('Miner stopped.')

# add_peer adds a new peer to known peers list. 
def add_peer(peer_address):
    # check if the address ends with a trailing slash and remove it        
    if peer_address.endswith('/'):
        peer_address = peer_address[:-1]

    # check if the peer is new
    if peer_address not in peers:
        logger.info("New peer added: %s", peer_address)
        # adds peer
        peers.append(peer_address)
    else:
        logger.info("Peer already registered: %s", peer_address)        

# this is our main
# checks if the port number is supplied
if len(sys.argv) != 2:
    print('Usage: python app.py PORT_NUMBER')
    raise SystemExit

# runs Flask server. Binding to 0.0.0.0 makes the server accessible to the outside network, so you can try
# connecting to other nodes! setting use_reloader to false ensures our Flask app does not restart if you change its code
app.run(host='0.0.0.0', debug=True, port=sys.argv[1], use_reloader=False)
