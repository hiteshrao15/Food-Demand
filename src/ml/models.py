"""Machine Learning Models for Food Demand Prediction.
Provides implementations of Linear Regression, Random Forest, and Deep Learning (Neural Network).
Works with scikit-learn / tensorflow if available, or high-performance native NumPy implementations.
"""
import numpy as np
import pandas as pd
import pickle
from typing import Dict, Any, Optional, Tuple

from src.utils.logger import get_logger
from src.config import RANDOM_STATE

logger = get_logger(__name__)

# Check if scikit-learn is available
try:
    from sklearn.linear_model import Ridge, LinearRegression as SklearnLR
    from sklearn.ensemble import RandomForestRegressor as SklearnRF
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Check if tensorflow is available
try:
    import tensorflow as tf
    from tensorflow import keras
    HAS_TF = True
except ImportError:
    HAS_TF = False


class NativeLinearRegression:
    """Ordinary Least Squares Linear Regression with Ridge Regularization."""
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.weights = None
        self.bias = 0.0
        self.coef_ = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        n_samples, n_features = X.shape

        # Add intercept column
        X_design = np.hstack([np.ones((n_samples, 1)), X])
        # Regularization matrix (do not regularize intercept)
        I = np.eye(n_features + 1)
        I[0, 0] = 0.0

        # Closed form solution: (X^T X + alpha * I)^(-1) X^T y
        try:
            beta = np.linalg.solve(X_design.T @ X_design + self.alpha * I, X_design.T @ y)
        except np.linalg.LinAlgError:
            beta = np.linalg.pinv(X_design.T @ X_design + self.alpha * I) @ (X_design.T @ y)

        self.bias = beta[0]
        self.weights = beta[1:]
        self.coef_ = self.weights
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        preds = X @ self.weights + self.bias
        # Demand cannot be negative
        return np.clip(preds, a_min=0, a_max=None)


class DecisionNode:
    """Node in a regression tree."""
    def __init__(self, feature=None, threshold=None, left=None, right=None, value=None):
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value


class NativeRegressionTree:
    """Fast Regression Decision Tree for Random Forest."""
    def __init__(self, max_depth: int = 12, min_samples_split: int = 4, max_features: Optional[int] = None):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.root = None

    def fit(self, X: np.ndarray, y: np.ndarray, rng: Optional[np.random.RandomState] = None):
        if rng is None:
            rng = np.random.RandomState(RANDOM_STATE)
        self.rng = rng
        self.root = self._build_tree(X, y, depth=0)
        return self

    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int) -> DecisionNode:
        n_samples, n_features = X.shape

        if depth >= self.max_depth or n_samples < self.min_samples_split or len(np.unique(y)) <= 1:
            return DecisionNode(value=float(np.mean(y)))

        # Subsample features if specified
        if self.max_features is not None and self.max_features < n_features:
            features = self.rng.choice(n_features, self.max_features, replace=False)
        else:
            features = np.arange(n_features)

        best_feat, best_thresh, best_var_red = None, None, 0.0
        current_var = np.var(y) * n_samples

        for feat in features:
            values = X[:, feat]
            # Use percentiles for fast threshold candidate selection
            thresholds = np.percentile(values, [20, 40, 60, 80])
            for thresh in thresholds:
                left_mask = values <= thresh
                right_mask = ~left_mask
                if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
                    continue

                var_left = np.var(y[left_mask]) * np.sum(left_mask)
                var_right = np.var(y[right_mask]) * np.sum(right_mask)
                var_red = current_var - (var_left + var_right)

                if var_red > best_var_red:
                    best_var_red = var_red
                    best_feat = feat
                    best_thresh = thresh

        if best_feat is None or best_var_red <= 1e-7:
            return DecisionNode(value=float(np.mean(y)))

        left_mask = X[:, best_feat] <= best_thresh
        left_child = self._build_tree(X[left_mask], y[left_mask], depth + 1)
        right_child = self._build_tree(X[~left_mask], y[~left_mask], depth + 1)

        return DecisionNode(feature=best_feat, threshold=best_thresh, left=left_child, right=right_child)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.array([self._predict_row(row, self.root) for row in X])

    def _predict_row(self, row: np.ndarray, node: DecisionNode) -> float:
        if node.value is not None:
            return node.value
        if row[node.feature] <= node.threshold:
            return self._predict_row(row, node.left)
        return self._predict_row(row, node.right)


class NativeRandomForestRegressor:
    """Random Forest Regressor with bagging and feature importance calculation."""
    def __init__(self, n_estimators: int = 40, max_depth: int = 12, max_features: Optional[int] = None, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.max_features = max_features
        self.random_state = random_state
        self.trees = []
        self.feature_importances_ = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        n_samples, n_features = X.shape

        rng = np.random.RandomState(self.random_state)
        max_feat = self.max_features or max(1, int(np.sqrt(n_features) * 1.5))

        self.trees = []
        feature_counts = np.zeros(n_features, dtype=np.float64)

        for _ in range(self.n_estimators):
            # Bootstrap sample
            indices = rng.choice(n_samples, n_samples, replace=True)
            X_boot, y_boot = X[indices], y[indices]

            tree = NativeRegressionTree(
                max_depth=self.max_depth,
                min_samples_split=4,
                max_features=max_feat
            )
            tree.fit(X_boot, y_boot, rng=rng)
            self.trees.append(tree)

            # Count feature usage for importance
            self._accumulate_feature_importance(tree.root, feature_counts)

        # Normalize feature importances
        total_counts = np.sum(feature_counts)
        if total_counts > 0:
            self.feature_importances_ = feature_counts / total_counts
        else:
            self.feature_importances_ = np.ones(n_features) / n_features

        return self

    def _accumulate_feature_importance(self, node: DecisionNode, counts: np.ndarray):
        if node is None or node.value is not None:
            return
        if node.feature is not None and node.feature < len(counts):
            counts[node.feature] += 1.0
        self._accumulate_feature_importance(node.left, counts)
        self._accumulate_feature_importance(node.right, counts)

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        all_preds = np.zeros((len(self.trees), len(X)))
        for i, tree in enumerate(self.trees):
            all_preds[i] = tree.predict(X)
        mean_preds = np.mean(all_preds, axis=0)
        return np.clip(mean_preds, a_min=0, a_max=None)


class NativeNeuralNetwork:
    """Multi-Layer Perceptron (Dense 64 -> ReLU -> Dense 32 -> ReLU -> Dense 1)."""
    def __init__(self, hidden_dim1: int = 64, hidden_dim2: int = 32, lr: float = 0.005, epochs: int = 40):
        self.hidden_dim1 = hidden_dim1
        self.hidden_dim2 = hidden_dim2
        self.lr = lr
        self.epochs = epochs
        self.W1, self.b1 = None, None
        self.W2, self.b2 = None, None
        self.W3, self.b3 = None, None

    def fit(self, X: np.ndarray, y: np.ndarray):
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).reshape(-1, 1)
        n_samples, n_features = X.shape

        rng = np.random.RandomState(RANDOM_STATE)
        # He initialization
        self.W1 = rng.randn(n_features, self.hidden_dim1) * np.sqrt(2.0 / n_features)
        self.b1 = np.zeros((1, self.hidden_dim1))
        self.W2 = rng.randn(self.hidden_dim1, self.hidden_dim2) * np.sqrt(2.0 / self.hidden_dim1)
        self.b2 = np.zeros((1, self.hidden_dim2))
        self.W3 = rng.randn(self.hidden_dim2, 1) * np.sqrt(2.0 / self.hidden_dim2)
        self.b3 = np.zeros((1, 1))

        batch_size = 64
        for epoch in range(self.epochs):
            perm = rng.permutation(n_samples)
            for i in range(0, n_samples, batch_size):
                idx = perm[i:i + batch_size]
                xb = X[idx]
                yb = y[idx]

                # Forward pass
                z1 = xb @ self.W1 + self.b1
                a1 = np.maximum(0, z1)  # ReLU
                z2 = a1 @ self.W2 + self.b2
                a2 = np.maximum(0, z2)  # ReLU
                y_hat = a2 @ self.W3 + self.b3

                # Loss gradient (MSE)
                m = len(xb)
                dy = (y_hat - yb) / m

                # Backprop
                dW3 = a2.T @ dy
                db3 = np.sum(dy, axis=0, keepdims=True)

                da2 = dy @ self.W3.T
                dz2 = da2 * (z2 > 0)
                dW2 = a1.T @ dz2
                db2 = np.sum(dz2, axis=0, keepdims=True)

                da1 = dz2 @ self.W2.T
                dz1 = da1 * (z1 > 0)
                dW1 = xb.T @ dz1
                db1 = np.sum(dz1, axis=0, keepdims=True)

                # Gradient clipping and weight update
                for grad in [dW1, db1, dW2, db2, dW3, db3]:
                    np.clip(grad, -1.0, 1.0, out=grad)

                self.W1 -= self.lr * dW1
                self.b1 -= self.lr * db1
                self.W2 -= self.lr * dW2
                self.b2 -= self.lr * db2
                self.W3 -= self.lr * dW3
                self.b3 -= self.lr * db3

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        z1 = X @ self.W1 + self.b1
        a1 = np.maximum(0, z1)
        z2 = a1 @ self.W2 + self.b2
        a2 = np.maximum(0, z2)
        out = (a2 @ self.W3 + self.b3).flatten()
        return np.clip(out, a_min=0, a_max=None)


def get_model(model_type: str, **kwargs):
    """Factory to instantiate the appropriate model."""
    if model_type == 'lr':
        if HAS_SKLEARN:
            return SklearnLR()
        return NativeLinearRegression(alpha=1.0)
    elif model_type == 'rf':
        if HAS_SKLEARN:
            return SklearnRF(n_estimators=kwargs.get('n_estimators', 100),
                             max_depth=kwargs.get('max_depth', 15),
                             random_state=RANDOM_STATE, n_jobs=-1)
        return NativeRandomForestRegressor(n_estimators=kwargs.get('n_estimators', 40),
                                          max_depth=kwargs.get('max_depth', 12),
                                          random_state=RANDOM_STATE)
    elif model_type == 'dl':
        return NativeNeuralNetwork(hidden_dim1=64, hidden_dim2=32, lr=0.005, epochs=kwargs.get('epochs', 40))
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
