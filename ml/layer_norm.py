import torch
from torch import Tensor
from torch import nn


def layer_norm(x: Tensor, eps: float) -> Tensor:
    x_mean = x.mean(dim=-1, keepdim=True)
    x_var = x.var(dim=-1, keepdim=True, unbiased=False)
    y = (x - x_mean) / (x_var + eps).sqrt()
    return y


def main():
    eps = 1e-5
    m = nn.LayerNorm(4, eps=eps, elementwise_affine=False)
    x = torch.randn(2, 3, 4)
    print("x", x)
    y1 = m(x)
    print("y1", y1)
    y2 = layer_norm(x, eps)
    print("y2", y2)
    assert float_equal(y1, y2)


def float_equal(a: Tensor, b: Tensor, eps: float = 1e-6) -> bool:
    assert a.size() == b.size()
    if a.size() == tuple():
        c = a.item() - b.item()
        if c < 0:
            c = -c
        return c < eps
    for i in range(a.size(0)):
        c = a[i]
        d = b[i]
        if not float_equal(c, d, eps):
            return False
    return True


if __name__ == "__main__":
    main()
