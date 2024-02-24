import json
import os
from openai import OpenAI
import requests
from datetime import datetime, timedelta
from flask import Flask
from flask import request
sk = "sk-"
first = "SEPe24kJ35OZckGKXPcNT3Blbk"
second = "FJJ2ivPRhrjax7UhMokT8W"
client = OpenAI(api_key=sk+first+second)

def check_eth_contract_verification(contract_address):
    url = f'https://api.etherscan.io/api'
    api_key = "USARF7XV11YDFSNCPZMEJUUERTUAYXDXFN"
    params_sourcecode = {
        'module': 'contract',
        'action': 'getsourcecode',
        'address': contract_address,
        'apikey': api_key,
    }
    try:
        response_sourcecode = requests.get(url, params=params_sourcecode)
        data_sourcecode = response_sourcecode.json()

        if data_sourcecode.get('status') == '1':
            return {
                'abi': data_sourcecode.get('result')[0].get('ABI'),
                'sourcecode': data_sourcecode.get('result')[0].get('SourceCode'),
                'proxy':data_sourcecode.get('result')[0].get('Proxy'),
                'contract_name':data_sourcecode.get('result')[0].get('ContractName'),
                'compiler':data_sourcecode.get('result')[0].get('ContractName')
            }
    except Exception as e:
        return False
    return False



def get_ca_functions(abi):
    function_names = []
    # Iterate over functions in the ABI
    for function_entry in abi:
        if function_entry['type'] == 'function':
            function_name = function_entry.get('name')
            if function_name:
                function_names.append(function_name)
    return function_names

def convert_to_dict(obj):
    if isinstance(obj, list):
        return [convert_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_to_dict(value) for key, value in obj.items()}
    elif hasattr(obj, '__dict__'):
        return {key: convert_to_dict(value) for key, value in obj.__dict__.items()}
    else:
        return obj

def compare_last_scan(latest_last_scan, new_last_scan):
    if not latest_last_scan:
        return new_last_scan

    changes = {}
    for key in new_last_scan:
        if key.startswith("last_"):
            new_value = new_last_scan[key]
            old_value = latest_last_scan.get(key, 0)

            if key in latest_last_scan:
                old_value = latest_last_scan[key]

            if key == 'last_block' and not isinstance(old_value, (int, float)):
                old_value = 0

            numeric_change = new_value - old_value

            percentage_change = ((numeric_change) / abs(old_value)) * 100 if old_value != 0 else 0

            if percentage_change == float('inf'):
                percentage_change = 0

            changes[key] = {"numeric_change": numeric_change, "percentage_change": percentage_change}

    return {"last_scan_changes": changes}





etherscan_api_key = "USARF7XV11YDFSNCPZMEJUUERTUAYXDXFN"
ETHERSCAN_API_BASE = "https://api.etherscan.io/api"
ANALYZE_DAYS = 90

def get_internal_transactions(wallet_address, start_block, end_block, page=1):
    params = {
        "module": "account",
        "action": "txlistinternal",
        "address": wallet_address,
        "startblock": start_block,
        "endblock": end_block,
        "page": page,
        "offset": 10,
        "sort": "desc",
        "apikey": etherscan_api_key,
    }

    response = requests.get(ETHERSCAN_API_BASE, params=params)
    result = response.json()

    if result["status"] == "1":
        return result["result"]
    else:
        return []

def get_normal_transactions(wallet_address, start_block, end_block, page=1):
    params = {
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": start_block,
        "endblock": end_block,
        "page": page,
        "offset": 10,
        "sort": "desc",
        "apikey": etherscan_api_key,
    }

    response = requests.get(ETHERSCAN_API_BASE, params=params)
    result = response.json()

    if result["status"] == "1":
        return result["result"]
    else:
        return []

def get_current_block():
    params = {
        "module": "proxy",
        "action": "eth_blockNumber",
        "apikey": etherscan_api_key,
    }

    response = requests.get(ETHERSCAN_API_BASE, params=params)
    result = response.json()

    if "result" in result:
        return int(result["result"], 16)
    else:
        return None


def get_block_number_3_months_ago():
    three_months_ago = datetime.now() - timedelta(days=int(ANALYZE_DAYS))
    timestamp_three_months_ago = int(three_months_ago.timestamp())
    block_number = get_block_number_by_timestamp(timestamp_three_months_ago)
    return block_number

def get_block_number_by_timestamp(timestamp):
    params = {
        "module": "block",
        "action": "getblocknobytime",
        "timestamp": timestamp,
        "closest": "before",
        "apikey": etherscan_api_key,
    }

    response = requests.get(ETHERSCAN_API_BASE, params=params)
    result = response.json()

    if result["status"] == "1" and "result" in result:
        return int(result["result"])

    return None




def get_ai_ca_transactions(ca_address, page=1):
    params = {
        "module": "account",
        "action": "txlist",
        "address": ca_address,
        "page": page,
        "offset": 20,
        "sort": "desc",
        "apikey": etherscan_api_key,
    }

    response = requests.get(ETHERSCAN_API_BASE, params=params)
    result = response.json()

    if result["status"] == "1":
        return result["result"]
    else:
        return []

def get_internal_ai_ca_transactions(ca_address, page=1):
    params = {
        "module": "account",
        "action": "txlistinternal",
        "address": ca_address,
        "page": page,
        "offset": 20,
        "sort": "desc",
        "apikey": etherscan_api_key,
    }

    response = requests.get(ETHERSCAN_API_BASE, params=params)
    result = response.json()

    if result["status"] == "1":
        return result["result"]
    else:
        return []




def extract_token_info(token):
    balance = token.get("balance", 0)

    return {
        "balance": balance,
        "contract_address": token.get("contract_address", ""),
        "decimals": token.get("contract_decimals", 0),
        "contract_name": token.get("contract_name", ""),
        "contract_ticker_symbol": token.get("contract_ticker_symbol", ""),
        "logo_url": token.get("logo_url", ""),
        "native_token": token.get("native_token", False),
        "pretty_quote": float(token.get("pretty_quote", "0").replace('$', '').replace(',', '')) if token.get("pretty_quote") is not None else 0,
        "quote_rate": token.get("quote_rate", 0.0),
    }

def calculate_total_quote(simplified_token_balances):
    total_quote = 0.0

    for token in simplified_token_balances:
        if token is not None:
            if not token["native_token"] and token["pretty_quote"] is not None:
                total_quote += token["pretty_quote"]

    return total_quote

def extract_transaction_info(transactions):
    total_gas_spent = sum(t.get("gas_spent", 0) for t in transactions)
    total_gas_quote = sum(float(t.get("gas_quote", 0)) for t in transactions)
    total_successful = sum(1 for t in transactions if t.get("successful", False))
    total_failed = sum(1 for t in transactions if not t.get("successful", False))
    total_value = sum(float(t.get("value_quote", 0)) for t in transactions)

    totals_dict = {
        "total_gas_spent": total_gas_spent,
        "total_gas_quote": total_gas_quote,
        "total_successful": total_successful,
        "total_failed": total_failed,
        "total_value": total_value,
    }

    return totals_dict

def convert_booleans(entry):
    if isinstance(entry, list):
        return [convert_booleans(item) for item in entry]
    elif isinstance(entry, dict):
        return {key: convert_booleans(value) for key, value in entry.items()}
    elif isinstance(entry, str) and entry.lower() in ('true', 'false'):
        return entry.lower() == 'true'
    return entry

def filter_approvals_ai(approvals):
    filtered_approvals = [
        {
            'balance_quote': item.get('balance_quote'),
            'spenders': [
                {
                    'allowance': spender.get('allowance'),
                    'block_signed_at': spender.get('block_signed_at'),
                    'risk_factor': spender.get('risk_factor'),

                }
                for spender in item.get('spenders', [])
            ],
            'ticker_symbol': item.get('ticker_symbol')
        }
        for item in approvals.get('items', [])
    ]
    return filtered_approvals


def extract_approvals_items(approvals):
    items = approvals.get("items", [])
    total_at_risk = sum(float(approval.get("pretty_value_at_risk_quote", "0").replace('$', '').replace(',', '')) if approval.get("pretty_value_at_risk_quote") is not None else 0 for approval in items)
    return {
        "items": items,
        "total_at_risk": total_at_risk
    }

def filter_spam_and_dust_items(data):
    if "items" in data:
        spam_items = [item for item in data["items"] if item.get("is_spam")]
        dust_items = [item for item in data["items"] if item.get("type") == "dust"]

        return {
            "spam_count": len(spam_items),
            "spam_items": spam_items,
            "dust_count": len(dust_items),
            "dust_items": dust_items
        }
    else:
        return {"spam_count": 0, "spam_items": [], "dust_count": 0, "dust_items": []}

def filter_spam_and_dust_items_ai(data):
    if "items" in data:
        spam_items = [item for item in data["items"] if item.get("is_spam")]

        # Adjusted filtering for dust items
        dust_items = [
            {
                'balance': item['balance'],
                'contract_name': item['contract_name'],
                'last_transferred_at': item['last_transferred_at']
            }
            for item in data["items"] if item.get("type") == "dust"
        ]

        return {
            "spam_count": len(spam_items),
            "spam_items": spam_items,
            "dust_count": len(dust_items),
            "dust_items": dust_items
        }
    else:
        return {"spam_count": 0, "spam_items": [], "dust_count": 0, "dust_items": []}

def compare_transaction_times(transactions, internal_transactions):
    if not transactions or not internal_transactions:
        return {"error": "No transactions or internal transactions provided"}

    latest_transaction_time = get_latest_timestamp(transactions)
    latest_internal_time = get_latest_timestamp(internal_transactions)

    if latest_transaction_time is None and latest_internal_time is None:
        return {"error": "No valid timestamps found"}

    if latest_transaction_time is None:
        latest_time = latest_internal_time
    elif latest_internal_time is None:
        latest_time = latest_transaction_time
    else:
        latest_time = max(latest_transaction_time, latest_internal_time)

    if latest_time is None:
        return {"error": "No valid timestamps found"}

    time_difference = datetime.now(timezone.utc) - latest_time
    days_ago = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    response = {
        "days_ago": days_ago,
        "hours_ago": hours,
        "minutes_ago": minutes,
        "seconds_ago": seconds,
        "sentence": f"The wallet was used {days_ago} days, {hours} hours, {minutes} minutes, and {seconds} seconds ago."
    }

    if days_ago >= 90:
        response["warning"] = "This wallet could be inactive."

    return response

def get_latest_timestamp(transactions):
    timestamps = [transaction.get("block_signed_at") for transaction in transactions if transaction.get("block_signed_at")]
    timestamps = [timestamp for timestamp in timestamps if timestamp]

    if timestamps:
        return max(timestamps)

    return None

def filter_token_balances(token_balances):
    filtered_balances = [
        {
            'balance': token.get('balance'),
            'contract_ticker_symbol': token.get('contract_ticker_symbol')
        }
        for token in token_balances.get("items", [])
    ]
    return filtered_balances

def filter_latest_transactions_for_ai(latest_transactions):
    filtered_transactions = [
        {
            'block_height': transaction.get('block_height'),
            'block_signed_at': transaction.get('block_signed_at'),
            'fees_paid': transaction.get('fees_paid'),
            'from_address': transaction.get('from_address'),
            'gas_spent': transaction.get('gas_spent'),
            'successful': transaction.get('successful'),
            'to_address': transaction.get('to_address'),
            'value': transaction.get('value'),
            'value_quote': transaction.get('value_quote'),
            'dex_details': transaction.get('dex_details'),
            'lending_details': transaction.get('lending_details'),
            'log_events': transaction.get('log_events')
        }
        for transaction in latest_transactions
    ]
    return filtered_transactions
def ai_analyze_contract(contract):
    # with open('contracts.json', 'r') as json_file:
        # weights = json.load(json_file)
    weights = json.loads("""{"contract_events": 6, "internal_transactions": 8, "code_metadata": 7, "account_transactions": 8, "contract_source_code": 9, "code_size": 7, "gas_usage": 8, "event_logs": 7, "smart_contract_calls": 8}""")
    # with open('contract_answers.json', 'r') as jsonx_file:
        # answer = json.load(jsonx_file)
    answer = json.loads("""{
  "functions": [
    {
      "name": "function_name",
      "explanation": "explanation_text"
    },
    {
      "name": "function_name",
      "explanation": "explanation_text"
    },
    {
      "name": "function_name",
      "explanation": "explanation_text"
    }
  ],
  "summary": [
    {
      "text": "summary_text",
      "safety_score": "calculated_score"
    }
  ]
}
""")
    cacode = check_eth_contract_verification(contract)

    if cacode != False:
        abi_list = json.loads(cacode.get('abi', []))
        abi_processed = [convert_booleans(entry) for entry in abi_list]
        function_names = get_ca_functions(abi_processed)
        source_code = cacode.get('sourcecode', '')
        catx = get_ai_ca_transactions(contract)
        caintx = get_internal_ai_ca_transactions(contract)

        prompt = (f"Given the Ethereum contract details and its functions listed below, "
              f"provide a detailed analysis in JSON format. The JSON should include "
              f"a 'functions' array with details about each function, and a 'summary' "
              f"object with the overall analysis text and a safety score. Use the following "
              f"structure for your response: {answer}. \n\n"
              f"Contract Source Code: {source_code}\n\n"
              f"Functions to analyze:\n")

        for function_name in function_names:
            prompt += f"- {function_name}\n"

        prompt += "\nInclude any relevant analysis based on the given transactions and internal transactions. and no less than 200 words:\n"
        prompt += f"Transactions: {catx}\nInternal Transactions: {caintx}\n"


        try:
            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": "You are a developer analyzing Ethereum contracts."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7
            )
            response_text = chat_completion.choices[0].message.content
            print(response_text)
            # print("Raw AI Response:", response_text)

            # Attempt to directly parse the AI response as JSON
            try:
                response_json = json.loads(response_text)
                print("Parsed JSON Response:", json.dumps(response_json, indent=4))
                return response_json
            except json.JSONDecodeError as e:
                print("Failed to parse AI response as JSON:", e)
                # Implement any fallback or post-processing here
        except Exception as e:
            print("An error occurred:", e)




app = Flask(__name__)

@app.route("/")
def home():
    address = request.args.get('address')
    # ai_analyze_contract("0x304645590f197d99fad9fa1d05e7bcdc563e1378")
    response = ai_analyze_contract(address)
    print(response)
    return response