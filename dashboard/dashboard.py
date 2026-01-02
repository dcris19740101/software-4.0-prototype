import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(
    page_title="Software 4.0 Demo",
    page_icon="🧠",
    layout="wide"
)

st.title("🚀 Software 4.0: Real-Time Fraud Detection")
st.markdown("### Where Business Logic Learns from Every Event")

def load_metrics():
    """Load metrics from shared volume"""
    try:
        with open('/app/data/metrics.json', 'r') as f:
            return json.load(f)
    except:
        return None

# Auto-refresh
placeholder = st.empty()

while True:
    metrics = load_metrics()
    
    if metrics and 'current' in metrics:
        with placeholder.container():
            current = metrics['current']
            
            # ============================================
            # CURRENT METRICS
            # ============================================
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric(
                "Transactions Processed",
                f"{current['transactions']:,}"
            )
            col2.metric(
                "Current Accuracy",
                f"{current['accuracy']:.1%}",
                help="Model improves as it learns from streaming data"
            )
            col3.metric(
                "Precision",
                f"{current['precision']:.1%}",
                help="% of fraud predictions that are correct"
            )
            col4.metric(
                "Recall",
                f"{current['recall']:.1%}",
                help="% of actual fraud cases detected"
            )
            
            # ============================================
            # ARCHITECTURE VISUALIZATION
            # ============================================
            st.markdown("---")
            st.markdown("### 🧠 Model Architecture: Two-Layer Design")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Constraint Layer",
                    f"{current['constraint_rejects']:,} decisions",
                    help="Hard business rules (regulatory, policy)"
                )
                st.markdown("**Hard Rules** (Frozen):")
                st.markdown("- Amount > $10,000 → REJECT")
                st.markdown("- Velocity > 50 tx/day → REJECT")
            
            with col2:
                st.metric(
                    "Adaptive Layer",
                    f"{current['adaptive_decisions']:,} decisions",
                    help="Learned patterns (continuously evolving)"
                )
                st.markdown("**Learned Patterns**:")
                st.markdown(f"- Tree depth: {current['tree_height']} levels")
                st.markdown(f"- Decision nodes: {current['tree_nodes']}")
                st.markdown(f"- Leaf nodes: {current['tree_leaves']}")
            
            with col3:
                constraint_pct = (current['constraint_rejects'] / 
                                max(current['transactions'], 1) * 100)
                adaptive_pct = (current['adaptive_decisions'] / 
                              max(current['transactions'], 1) * 100)
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Constraint Layer', 'Adaptive Layer'],
                    values=[constraint_pct, adaptive_pct],
                    hole=.3,
                    marker_colors=['#ff6b6b', '#4ecdc4']
                )])
                fig_pie.update_layout(
                    title="Decision Distribution",
                    height=250,
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # ============================================
            # LEARNING VISUALIZATION
            # ============================================
            if 'history' in metrics and len(metrics['history']) > 0:
                st.markdown("---")
                
                df = pd.DataFrame(metrics['history'])
                
                # Main accuracy chart with pattern shift annotation
                fig_acc = px.line(
                    df,
                    x='transactions',
                    y='accuracy',
                    title='📈 Model Learning: Accuracy Improves Over Time',
                    labels={'transactions': 'Transactions Processed', 'accuracy': 'Accuracy'}
                )
                
                # Add pattern shift marker
                fig_acc.add_vline(
                    x=500,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Fraud Pattern Shifts →",
                    annotation_position="top left"
                )
                
                fig_acc.add_annotation(
                    x=650,
                    y=df['accuracy'].min() + 0.1,
                    text="Model adapts automatically<br>to new fraud tactics",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="green",
                    bgcolor="lightgreen",
                    opacity=0.8
                )
                
                fig_acc.update_layout(height=400)
                st.plotly_chart(fig_acc, use_container_width=True)
                
                # Precision & Recall
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_prec = px.line(
                        df,
                        x='transactions',
                        y='precision',
                        title='🎯 Precision: Improving Accuracy of Fraud Predictions'
                    )
                    fig_prec.update_layout(height=300)
                    st.plotly_chart(fig_prec, use_container_width=True)
                
                with col2:
                    fig_rec = px.line(
                        df,
                        x='transactions',
                        y='recall',
                        title='🔍 Recall: Catching More Fraud Cases'
                    )
                    fig_rec.update_layout(height=300)
                    st.plotly_chart(fig_rec, use_container_width=True)
            
            # ============================================
            # EXPLANATION
            # ============================================
            st.markdown("---")
            st.markdown("### 🎯 This is Software 4.0")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **What You're Seeing:**
                - ✅ Model trains **continuously** from every transaction
                - ✅ No batch retraining pipeline needed
                - ✅ Business rules adapt **automatically**
                - ✅ Deterministic predictions (<10ms latency)
                - ✅ Full auditability (decision tree rules)
                - ✅ Pattern shift at transaction 500: model adapts in ~2 minutes
                
                **Architecture:**
```
                Kafka Stream → Constrained Hoeffding Tree → Predictions
                               (learns from every event)
```
                """)
            
            with col2:
                st.markdown("""
                **The Paradigm Shift:**
                
                **Software 3.0** (Andrej Karpathy):
                - LLMs help you BUILD applications faster
                - Natural language as programming interface
                - Revolutionizes software DEVELOPMENT
                
                **Software 4.0** (This Demo):
                - Applications LEARN at runtime from events
                - Business logic adapts continuously
                - Revolutionizes software OPERATIONS
                
                **Where Software 3.0 stops, Software 4.0 begins.**
                """)
            
            st.markdown("---")
            st.markdown("""
            ### 🏢 Production Examples
            
            This isn't theoretical - companies already do this:
            - **Netflix**: Continuous learning for recommendations
            - **Uber**: Real-time fraud detection & dynamic pricing
            - **LinkedIn**: Feed ranking with online learning
            - **Google Ads**: CTR prediction (billions of events/day)
            
            **Different domains, same pattern: constraints + continuous learning**
            """)
            
            st.markdown("---")
            st.markdown("""
            <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
                <h3>🔗 Learn More</h3>
                <p><strong>Repository:</strong> <a href='https://github.com/YOUR_USERNAME/software-4.0-prototype'>GitHub</a></p>
                <p><strong>Foundation:</strong> <a href='https://github.com/YOUR_USERNAME/ml-fundamentals'>ML Fundamentals</a></p>
                <p><strong>Creator:</strong> <a href='https://www.linkedin.com/in/christian-dubois-confluent'>Christian Dubois</a></p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.warning("⏳ Waiting for data... Make sure Kafka and consumer are running.")
    
    time.sleep(2)  # Refresh every 2 seconds
