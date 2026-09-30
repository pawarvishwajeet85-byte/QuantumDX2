"""Phase 0 verification: real versions + real VQC smoke test. No fabricated output."""
import importlib, sys, time

print("python", sys.version.split()[0])
for pkg in ["numpy", "pandas", "scipy", "sklearn", "pennylane", "fastapi",
            "pydantic", "sqlalchemy", "alembic", "argon2", "shap"]:
    try:
        m = importlib.import_module(pkg)
        print(f"{pkg:12s}", getattr(m, "__version__", "installed (no __version__)"))
    except Exception as e:
        print(f"{pkg:12s} MISSING/BROKEN -> {type(e).__name__}: {e}")

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp
from sklearn.datasets import load_breast_cancer
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler

SEED, N_Q, N_L = 42, 4, 3
X, y = load_breast_cancer(return_X_y=True)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
sc = StandardScaler().fit(Xtr); pca = PCA(N_Q, random_state=SEED).fit(sc.transform(Xtr))  # train only
Ztr = pca.transform(sc.transform(Xtr)); Zte = pca.transform(sc.transform(Xte))
mm = MinMaxScaler((0, np.pi)).fit(Ztr)
Ztr = mm.transform(Ztr); Zte = np.clip(mm.transform(Zte), 0, np.pi)
ytr_pm, yte_pm = 2 * ytr - 1, 2 * yte - 1

dev = qml.device("default.qubit", wires=N_Q)

@qml.qnode(dev, interface="autograd", diff_method="backprop")
def circuit(x, w):
    qml.AngleEmbedding(x, wires=range(N_Q), rotation="Y")
    qml.StronglyEntanglingLayers(w, wires=range(N_Q))
    return qml.expval(qml.PauliZ(0))

shape = qml.StronglyEntanglingLayers.shape(n_layers=N_L, n_wires=N_Q)
rng = np.random.default_rng(SEED)
w = pnp.array(rng.uniform(0, 2 * np.pi, shape), requires_grad=True)

try:
    batched = np.asarray(circuit(Ztr[:8], w)); assert batched.shape == (8,)
    predict = lambda X_, w_: circuit(X_, w_); print("broadcasting: OK")
except Exception as e:
    print("broadcasting: NOT available ->", type(e).__name__, "(using loop)")
    predict = lambda X_, w_: pnp.stack([circuit(x, w_) for x in X_])

def loss(w_, Xb, yb): return pnp.mean((predict(Xb, w_) - yb) ** 2)

opt, t0, losses = qml.AdamOptimizer(0.1), time.time(), []
idx = np.random.default_rng(SEED)
for step in range(30):
    b = idx.choice(len(Ztr), 32, replace=False)
    w, l = opt.step_and_cost(lambda v: loss(v, pnp.array(Ztr[b], requires_grad=False), ytr_pm[b]), w)
    losses.append(float(l))
print(f"train time {time.time()-t0:.1f}s | loss first/last: {losses[0]:.3f} -> {losses[-1]:.3f}")
pred = np.sign(np.asarray(predict(Zte, w)))
print("smoke-test holdout acc (NOT a reported result):", float((pred == yte_pm).mean()))
print("circuit:\n", qml.draw(circuit)(Ztr[0], w))
assert losses[-1] < losses[0], "loss did not decrease: investigate before proceeding"
print("PHASE0 QUANTUM SMOKE TEST: PASS")
