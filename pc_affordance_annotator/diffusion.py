import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import lil_matrix, diags, identity
from scipy.sparse.linalg import spsolve


def ground_truth_construction(sampled_points, key_points, k, alpha):
    """基于3D AffordanceNet真值构建方法生成可供性概率分数"""
    tree = cKDTree(sampled_points)
    distances, indices = tree.query(sampled_points, k=k + 1)
    indices = indices[:, 1:]
    distances = distances[:, 1:]

    N = sampled_points.shape[0]
    A = lil_matrix((N, N))
    for i in range(N):
        A[i, indices[i]] = distances[i]
    
    W = 0.5 * (A + A.T)
    d_inv_sqrt_arr = 1.0 / np.sqrt(np.array(W.sum(axis=1)).flatten() + 1e-8)
    D_inv_sqrt = diags(d_inv_sqrt_arr)
    W_tilde = D_inv_sqrt @ W @ D_inv_sqrt

    Y = np.zeros(N)
    for key in key_points:
        _, idx = tree.query(key, k=1)
        Y[idx] = 1.0

    I = identity(N)
    S = spsolve(I - alpha * W_tilde, Y)
    S = (S - S.min()) / (S.max() - S.min() + 1e-8)
    return S
