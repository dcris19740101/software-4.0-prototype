import json
import time
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from river import metrics
import os

from constrained_tree import HoeffdingTreeWithConstraints

# ============================================
# HARD CONSTRAINTS (Business Rules)
# ============================================
HARD_CONSTRAINTS = [
    {
        'feature': 'amount',
        'threshold': 10000,
        'operator': 'greater',
        'reason': 'Exceeds regulatory limit ($10,000)'
    },
    {
        'feature': 'velocity',
        'threshold': 50,
        'operator': 'greater',
        'reason': 'Exceeds daily transaction limit (50)'
    }
]

# ============================================
# THE BRAIN
# ============================================
class BusinessLogicBrain:
    """
    The BRAIN of the microservice.
    ONE model containing ALL business logic:
    - Hard constraints (frozen nodes)
    - Adaptive patterns (learnable nodes)
    """
    
    def __init__(self, constraints):
        # Updated parameters for River's current API
        self.model = HoeffdingTreeWithConstraints(
            constraints=constraints,
            grace_period=200,
            delta=1e-5,  # Changed from split_confidence
            tau=0.05,
            leaf_prediction='nb'
        )
        
        self.accuracy = metrics.Accuracy()
        self.precision = metrics.Precision()
        self.recall = metrics.Recall()
        self.transactions_processed = 0
    
    def predict(self, features):
        """Ask the brain for a decision"""
        prediction = self.model.predict_one(features)
        probabilities = self.model.predict_proba_one(features)
        
        return {
            'is_fraud': prediction,
            'fraud_probability': probabilities.get(True, 0.0)
        }
    
    def learn(self, features, actual_is_fraud):
        """Teach the brain from outcomes"""
        prediction = self.model.predict_one(features)
        
        self.accuracy.update(actual_is_fraud, prediction)
        self.precision.update(actual_is_fraud, prediction)
        self.recall.update(actual_is_fraud, prediction)
        
        self.model.learn_one(features, actual_is_fraud)
        self.transactions_processed += 1
    
    def get_stats(self):
        """Get brain statistics"""
        return {
            'transactions': self.transactions_processed,
            'accuracy': self.accuracy.get(),
            'precision': self.precision.get(),
            'recall': self.recall.get(),
            'constraint_rejects': self.model.n_constraint_rejects,
            'adaptive_decisions': self.model.n_adaptive_decisions,
            'tree_height': self.model.height,
            'tree_nodes': self.model.n_nodes,
            'tree_leaves': self.model.n_leaves
        }
    
    def describe(self):
        """Human-readable model structure"""
        return self.model.describe()

# ============================================
# FEATURE EXTRACTION
# ============================================
def extract_features(transaction):
    """Extract features (no constraint encoding needed!)"""
    try:
        timestamp = datetime.fromisoformat(transaction['timestamp'])
        hour = timestamp.hour
    except:
        hour = 12
    
    return {
        'amount': float(transaction['amount']),
        'velocity': float(transaction['velocity']),
        'location_change': 1 if transaction.get('location_change', False) else 0,
        'hour_of_day': hour
    }

# ============================================
# MICROSERVICE
# ============================================
def create_consumer(bootstrap_servers, topic, retries=10):
    """Create Kafka consumer with retry logic"""
    for i in range(retries):
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                group_id='fraud-detector'
            )
            print(f"✓ Connected to Kafka at {bootstrap_servers}")
            return consumer
        except NoBrokersAvailable:
            print(f"⟳ Waiting for Kafka... ({i+1}/{retries})")
            time.sleep(5)
    raise Exception("Could not connect to Kafka")

def save_metrics(metrics_data):
    """Save metrics for dashboard"""
    os.makedirs('/app/data', exist_ok=True)
    with open('/app/data/metrics.json', 'w') as f:
        json.dump(metrics_data, f)

def main():
    print("🧠 Starting Software 4.0 Microservice")
    print("=" * 80)
    print("Architecture: Lightweight microservice + Brain (unified model)")
    print("=" * 80)
    
    # Initialize THE BRAIN
    brain = BusinessLogicBrain(HARD_CONSTRAINTS)
    print(f"\n{brain.describe()}")
    
    # Connect to Kafka
    bootstrap_servers = 'kafka:29092'
    topic = 'transactions'
    consumer = create_consumer(bootstrap_servers, topic)
    
    print(f"\n💡 Microservice Running")
    print(f"   Code: ~20 lines (rest is in the brain)")
    print(f"   Processing transactions from '{topic}'...")
    print("=" * 80)
    print(f"{'Trans':<8} {'Decision':<10} {'Confidence':<12} {'Accuracy':<10} {'Layer':<15}")
    print("=" * 80)
    
    metrics_history = []
    
    try:
        for message in consumer:
            transaction = message.value
            
            # ============================================
            # MICROSERVICE LOGIC (3 lines!)
            # ============================================
            features = extract_features(transaction)
            decision = brain.predict(features)
            brain.learn(features, transaction['is_fraud'])
            # ============================================
            
            stats = brain.get_stats()
            
            if stats['transactions'] % 5 == 0:
                # Determine layer
                was_constraint = (
                    features['amount'] > 10000 or 
                    features['velocity'] > 50
                )
                layer = 'CONSTRAINT' if was_constraint else 'ADAPTIVE'
                
                print(f"{stats['transactions']:<8} "
                      f"{'FRAUD' if decision['is_fraud'] else 'LEGIT':<10} "
                      f"{decision['fraud_probability']:<12.2%} "
                      f"{stats['accuracy']:<10.3f} "
                      f"{layer:<15}")
                
                # Save metrics
                metrics_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'transactions': stats['transactions'],
                    'accuracy': stats['accuracy'],
                    'precision': stats['precision'],
                    'recall': stats['recall'],
                    'constraint_rejects': stats['constraint_rejects'],
                    'adaptive_decisions': stats['adaptive_decisions']
                })
                
                if len(metrics_history) > 1000:
                    metrics_history = metrics_history[-1000:]
                
                save_metrics({
                    'current': stats,
                    'history': metrics_history
                })
            
            if stats['transactions'] % 100 == 0:
                print(f"\n{brain.describe()}\n")
                print("=" * 80)
    
    except KeyboardInterrupt:
        print(f"\n\n{brain.describe()}")
        consumer.close()

if __name__ == "__main__":
    main()
