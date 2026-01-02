"""
Constrained Hoeffding Tree: Decision tree with frozen constraint nodes.

This implements Software 4.0 architecture where:
- Top layers: Frozen constraint nodes (business rules)
- Bottom layers: Learnable Hoeffding Tree (adaptive patterns)
"""

from river import tree


class ConstraintNode:
    """
    A frozen decision node representing a hard business constraint.
    This node NEVER changes or re-learns.
    """
    
    def __init__(self, feature, threshold, reject_direction='greater', reason=''):
        self.feature = feature
        self.threshold = threshold
        self.reject_direction = reject_direction
        self.reason = reason
        self.is_frozen = True
        
        # Children - continue_child will be set later
        self.continue_child = None
    
    def predict_one(self, x):
        """Make decision based on constraint"""
        value = x.get(self.feature, 0)
        
        if self.reject_direction == 'greater':
            violates = value > self.threshold
        else:
            violates = value < self.threshold
        
        if violates:
            return True  # Constraint violated → fraud
        else:
            if self.continue_child:
                return self.continue_child.predict_one(x)
            else:
                return False
    
    def predict_proba_one(self, x):
        """Return probability distribution"""
        value = x.get(self.feature, 0)
        
        if self.reject_direction == 'greater':
            violates = value > self.threshold
        else:
            violates = value < self.threshold
        
        if violates:
            return {True: 1.0, False: 0.0}  # 100% fraud
        else:
            if self.continue_child:
                return self.continue_child.predict_proba_one(x)
            else:
                return {True: 0.0, False: 1.0}
    
    def learn_one(self, x, y, **kwargs):
        """
        Constraint nodes don't learn!
        Pass learning to the learnable subtree.
        """
        value = x.get(self.feature, 0)
        
        if self.reject_direction == 'greater':
            violates = value > self.threshold
        else:
            violates = value < self.threshold
        
        if not violates and self.continue_child:
            self.continue_child.learn_one(x, y, **kwargs)


class HoeffdingTreeWithConstraints:
    """
    Hoeffding Tree initialized with hard constraint nodes.
    
    Architecture:
    - Top layers: Frozen constraint nodes (never change)
    - Bottom layers: Learnable Hoeffding Tree (adapts continuously)
    
    This is the "brain" of Software 4.0 - ALL business logic in ONE model.
    """
    
    def __init__(self, constraints=None, **hoeffding_params):
        """
        Args:
            constraints: List of constraint dicts:
                - feature: str (feature name)
                - threshold: float (threshold value)
                - operator: str ('greater' or 'less')
                - reason: str (human-readable reason)
            hoeffding_params: Parameters for learnable tree
        """
        self.constraints = constraints or []
        self.hoeffding_params = hoeffding_params
        
        # Build tree with constraints at top
        self._root = self._build_constraint_tree()
        
        # Statistics
        self.n_constraint_rejects = 0
        self.n_adaptive_decisions = 0
        self._total_predictions = 0
    
    def _build_constraint_tree(self):
        """Build constraint chain with learnable tree at bottom"""
        
        if not self.constraints:
            return tree.HoeffdingTreeClassifier(**self.hoeffding_params)
        
        # Build chain of constraint nodes
        root = None
        current = None
        
        for constraint in self.constraints:
            node = ConstraintNode(
                feature=constraint['feature'],
                threshold=constraint['threshold'],
                reject_direction=constraint.get('operator', 'greater'),
                reason=constraint.get('reason', '')
            )
            
            if root is None:
                root = node
                current = node
            else:
                current.continue_child = node
                current = node
        
        # Attach learnable Hoeffding Tree at bottom
        current.continue_child = tree.HoeffdingTreeClassifier(**self.hoeffding_params)
        
        return root
    
    def predict_one(self, x):
        """Predict using constraint + learnable tree"""
        self._total_predictions += 1
        return self._root.predict_one(x)
    
    def predict_proba_one(self, x):
        """Return probability distribution"""
        return self._root.predict_proba_one(x)
    
    def learn_one(self, x, y, **kwargs):
        """Learn only in learnable nodes (constraints are frozen)"""
        self._root.learn_one(x, y, **kwargs)
        
        if self._was_rejected_by_constraint(x):
            self.n_constraint_rejects += 1
        else:
            self.n_adaptive_decisions += 1
    
    def _was_rejected_by_constraint(self, x):
        """Check if any constraint was violated"""
        for constraint in self.constraints:
            value = x.get(constraint['feature'], 0)
            threshold = constraint['threshold']
            operator = constraint.get('operator', 'greater')
            
            if operator == 'greater' and value > threshold:
                return True
            elif operator == 'less' and value < threshold:
                return True
        
        return False
    
    @property
    def height(self):
        """Tree height"""
        learnable_tree = self._get_learnable_tree()
        if hasattr(learnable_tree, 'height'):
            return len(self.constraints) + learnable_tree.height
        return len(self.constraints) + 1
    
    @property
    def n_nodes(self):
        """Total number of nodes"""
        learnable_tree = self._get_learnable_tree()
        constraint_nodes = len(self.constraints)
        if hasattr(learnable_tree, 'n_nodes'):
            return constraint_nodes + learnable_tree.n_nodes
        return constraint_nodes + 1
    
    @property
    def n_leaves(self):
        """Number of leaf nodes"""
        learnable_tree = self._get_learnable_tree()
        if hasattr(learnable_tree, 'n_leaves'):
            return learnable_tree.n_leaves
        return 1
    
    def _get_learnable_tree(self):
        """Navigate to the learnable Hoeffding Tree"""
        current = self._root
        while isinstance(current, ConstraintNode):
            current = current.continue_child
        return current
    
    def describe(self):
        """Human-readable tree structure"""
        lines = ["🧠 Model Structure:"]
        lines.append("\n📋 CONSTRAINT LAYER (Frozen - Business Rules):")
        
        for i, constraint in enumerate(self.constraints, 1):
            op = '>' if constraint.get('operator', 'greater') == 'greater' else '<'
            lines.append(
                f"   {i}. IF {constraint['feature']} {op} {constraint['threshold']} "
                f"→ REJECT"
            )
            if constraint.get('reason'):
                lines.append(f"      Reason: {constraint['reason']}")
        
        lines.append("\n🎯 ADAPTIVE LAYER (Learns from Data):")
        learnable_tree = self._get_learnable_tree()
        
        if hasattr(learnable_tree, 'n_nodes'):
            lines.append(f"   - Decision nodes: {learnable_tree.n_nodes}")
            lines.append(f"   - Leaf nodes: {learnable_tree.n_leaves}")
            lines.append(f"   - Tree depth: {learnable_tree.height}")
        else:
            lines.append("   - Ready to learn (no patterns yet)")
        
        lines.append(f"\n📊 Decision Statistics:")
        lines.append(f"   - Constraint rejects: {self.n_constraint_rejects}")
        lines.append(f"   - Adaptive decisions: {self.n_adaptive_decisions}")
        
        return "\n".join(lines)
