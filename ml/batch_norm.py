import torch
from torch import Tensor
from torch import nn


def batch_norm1d(x: Tensor, eps: float) -> Tensor:
    if len(x.size()) == 2:
        x_mean = x.mean([0])
        x_var = x.var([0], unbiased=False)
        y = (x - x_mean[None, :]) / (x_var[None, :] + eps).sqrt()
        return y
    elif len(x.size()) == 3:
        x_mean = x.mean([0, 2])
        x_var = x.var([0, 2], unbiased=False)
        y = (x - x_mean[None, :, None]) / (x_var[None, :, None] + eps).sqrt()
        return y
    else:
        raise ValueError("only support 2d or 3d")


def main():
    eps = 1e-5
    m = nn.BatchNorm1d(4, eps=eps, affine=False)
    x = torch.randn(2, 4)
    print("x", x)
    y1 = m(x)
    print("y1", y1)
    y2 = batch_norm1d(x, eps)
    print("y2", y2)
    assert float_equal(y1, y2)

    x = torch.randn(2, 4, 3)
    print("x", x)
    y1 = m(x)
    print("y1", y1)
    y2 = batch_norm1d(x, eps)
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
