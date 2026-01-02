import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

def create_producer(bootstrap_servers, retries=10):
    """Create Kafka producer with retry logic"""
    for i in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print(f"✓ Connected to Kafka at {bootstrap_servers}")
            return producer
        except NoBrokersAvailable:
            print(f"⟳ Waiting for Kafka... ({i+1}/{retries})")
            time.sleep(5)
    raise Exception("Could not connect to Kafka")

def generate_transaction(transaction_id):
    """
    Generate synthetic transaction with evolving fraud patterns.
    
    Pattern shift at transaction 500:
    - Early (0-500): High amount fraud
    - Late (500+): High velocity fraud (fraudsters adapted!)
    """
    
    is_fraud = random.random() < 0.1  # 10% fraud rate
    
    # 5% of transactions violate hard constraints
    violates_constraint = random.random() < 0.05
    
    if violates_constraint:
        # Hard constraint violation (these are ALWAYS fraud)
        if random.random() < 0.5:
            # Regulatory violation: amount > $10,000
            amount = random.uniform(10001, 15000)
            velocity = random.randint(1, 10)
        else:
            # Business policy violation: velocity > 50
            amount = random.uniform(100, 1000)
            velocity = random.randint(51, 100)
        
        is_fraud = True
        
    elif transaction_id < 500:
        # EARLY PATTERN: High amount = fraud
        if is_fraud:
            amount = random.uniform(1500, 3000)
            velocity = random.randint(5, 10)
        else:
            amount = random.uniform(10, 500)
            velocity = random.randint(1, 5)
            
    else:
        # LATE PATTERN: High velocity = fraud (pattern shift!)
        if is_fraud:
            amount = random.uniform(400, 700)  # Lower amounts
            velocity = random.randint(15, 25)  # Much higher velocity!
        else:
            amount = random.uniform(10, 500)
            velocity = random.randint(1, 5)
    
    location_change = random.choice([True, False]) if is_fraud else False
    
    return {
        'transaction_id': transaction_id,
        'timestamp': datetime.now().isoformat(),
        'amount': round(amount, 2),
        'velocity': velocity,
        'location_change': location_change,
        'is_fraud': is_fraud,
        'pattern_era': 'early' if transaction_id < 500 else 'evolved'
    }

def main():
    print("🚀 Starting Software 4.0 Transaction Producer")
    print("=" * 80)
    
    bootstrap_servers = 'kafka:29092'
    topic = 'transactions'
    
    producer = create_producer(bootstrap_servers)
    
    print(f"\n📊 Generating transactions to topic '{topic}'")
    print("=" * 80)
    print("Pattern Evolution:")
    print("  Transactions 0-500:   High amount fraud ($1500-3000)")
    print("  Transactions 500+:    High velocity fraud (15-25 tx/hour)")
    print("  Constraints (always): Amount > $10K OR velocity > 50")
    print("=" * 80)
    print(f"{'Trans':<8} {'Amount':<10} {'Velocity':<10} {'Fraud':<8} {'Pattern':<12}")
    print("=" * 80)
    
    transaction_id = 0
    transactions_sent = 0
    fraud_count = 0
    
    try:
        while True:
            transaction = generate_transaction(transaction_id)
            
            producer.send(topic, value=transaction)
            
            transactions_sent += 1
            if transaction['is_fraud']:
                fraud_count += 1
            
            # Pattern shift announcement
            if transaction_id == 500:
                print("\n" + "=" * 80)
                print("🔄 FRAUD PATTERN SHIFT!")
                print("   Fraudsters changed tactics from high amounts to high velocity")
                print("   Watch the model adapt automatically in the dashboard...")
                print("=" * 80)
                print(f"{'Trans':<8} {'Amount':<10} {'Velocity':<10} {'Fraud':<8} {'Pattern':<12}")
                print("=" * 80)
            
            # Log every 10 transactions
            if transactions_sent % 10 == 0:
                fraud_rate = (fraud_count / transactions_sent) * 100
                print(f"{transaction_id:<8} "
                      f"${transaction['amount']:<9.2f} "
                      f"{transaction['velocity']:<10} "
                      f"{'YES' if transaction['is_fraud'] else 'NO':<8} "
                      f"{transaction['pattern_era']:<12}")
            
            transaction_id += 1
            time.sleep(0.5)  # 2 transactions per second
            
    except KeyboardInterrupt:
        print(f"\n\n✓ Sent {transactions_sent} transactions ({fraud_count} fraudulent)")
        producer.close()

if __name__ == "__main__":
    main()
