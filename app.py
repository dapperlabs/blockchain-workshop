from flask import Flask, request
from blockchain import Block
import requests
import json
import sys

from node import Node

app =  Flask(__name__)

node = Node()

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    req_data = request.get_json()
    required_fields = ['transaction']

    for field in required_fields:
        if not req_data.get(field):
            return 'Invalid request: missing field transaction', 400    

    node.new_transaction(req_data)

    return 'Success', 201

@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    blockchain = []
    for block in node.blockchain.blocks:
        blockchain.append(block.__dict__)
    return json.dumps({'length': len(blockchain),
                       'blockchain': blockchain})

@app.route('/mine', methods=['GET'])
def mine_transaction_pool():
    result = node.mine()
    if not result:
        return 'Transaction pool is empty'
    else:
        chain_length = len(node.blockchain)
        node.consensus()
        if chain_length == len(node.blockchain.chain):            
            node.announce_new_block(node.blockchain.get_last_block)
        return "Block #{} is mined.".format(node.blockchain.get_last_block.index)    

@app.route('/tx_pool', methods=['GET'])
def get_tx_pool():
    return json.dumps(node.transaction_pool)

@app.route('/greet', methods=['POST'])
def greet():    
    peer_address = request.get_json()['address']
    if not peer_address:
        return 'Missing address', 400

    node.add_peer(peer_address)

    return get_blockchain()

@app.route('/sync_peer', methods=['POST'])
def sync_with_peer():    
    peer_address = request.get_json()['address']
    if not peer_address:
        return 'Missing address', 400

    data = {'peer_address': request.host_url}
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(peer_address + '/greet',
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:        
        chain_dump = response.json()['blockchain']        
        node.sync_with_dump(chain_dump)
        node.update_peers(response.json()['peers'])        
        return 'Sync successful', 200
    else:        
        return response.content, response.status_code

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

if len(sys.argv) != 2:
    print('Usage: python app.py PORT_NUMBER')
    raise SystemExit

app.run(debug=True, port=sys.argv[1])