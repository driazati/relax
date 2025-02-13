# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import pytest
import tvm
import tvm.testing
from tvm import relax, tir
from tvm import TVMError
from tvm.ir import Op
from tvm.script import relax as R


def test_op_correctness():
    x = relax.Var("x", R.Tensor((2, 3, 28, 28), "float32"))
    w = relax.Var("w", R.Tensor((4, 3, 3, 3), "float32"))
    assert relax.op.nn.conv2d(x, w).op == Op.get("relax.nn.conv2d")


def _check_inference(bb: relax.BlockBuilder, call: relax.Call, expected_sinfo: relax.StructInfo):
    ret = bb.normalize(call)
    tvm.ir.assert_structural_equal(ret.struct_info, expected_sinfo)


def test_conv2d_infer_struct_info():
    bb = relax.BlockBuilder()
    x0 = relax.Var("x", R.Tensor((2, 3, 28, 28), "float32"))
    x1 = relax.Var("x", R.Tensor((2, 28, 28, 3), "float32"))
    x2 = relax.Var("x", R.Tensor("float32", ndim=4))
    x3 = relax.Var("x", R.Tensor("float32"))
    x4 = relax.Var("x", R.Tensor())
    x5 = relax.Var("x", R.Tensor((2, 4, 28, 28, 16), "float32"))
    w0 = relax.Var("w", R.Tensor((4, 3, 3, 3), "float32"))
    w1 = relax.Var("w", R.Tensor((3, 4, 3, 3), "float32"))
    w2 = relax.Var("w", R.Tensor("float32", ndim=4))
    w3 = relax.Var("w", R.Tensor("float32"))
    w4 = relax.Var("w", R.Tensor((48, 4, 3, 3, 16), "float32"))

    _check_inference(
        bb, relax.op.nn.conv2d(x0, w0), relax.TensorStructInfo((2, 4, 26, 26), "float32")
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w0, out_dtype="float16"),
        relax.TensorStructInfo((2, 4, 26, 26), "float16"),
    )
    _check_inference(
        bb, relax.op.nn.conv2d(x0, w0, padding=1), relax.TensorStructInfo((2, 4, 28, 28), "float32")
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w0, padding=[1, 2]),
        relax.TensorStructInfo((2, 4, 28, 30), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w0, padding=[1, 2, 3, 4]),
        relax.TensorStructInfo((2, 4, 30, 32), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w0, strides=2),
        relax.TensorStructInfo((2, 4, 13, 13), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w0, strides=(2, 3)),
        relax.TensorStructInfo((2, 4, 13, 9), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w0, dilation=2),
        relax.TensorStructInfo((2, 4, 24, 24), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w0, dilation=(2, 1)),
        relax.TensorStructInfo((2, 4, 24, 26), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x1, w0, data_layout="NHWC"),
        relax.TensorStructInfo((2, 26, 26, 4), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w0, out_layout="NHWC"),
        relax.TensorStructInfo((2, 26, 26, 4), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w1, kernel_layout="IOHW"),
        relax.TensorStructInfo((2, 4, 26, 26), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(
            x5, w4, data_layout="NCHW16c", kernel_layout="OIHW16i", out_layout="NHWC16c"
        ),
        relax.TensorStructInfo((2, 26, 26, 3, 16), "float32"),
    )
    _check_inference(
        bb, relax.op.nn.conv2d(x2, w0), relax.TensorStructInfo(dtype="float32", ndim=4)
    )
    _check_inference(
        bb, relax.op.nn.conv2d(x3, w0), relax.TensorStructInfo(dtype="float32", ndim=4)
    )
    _check_inference(
        bb, relax.op.nn.conv2d(x0, w2), relax.TensorStructInfo(dtype="float32", ndim=4)
    )
    _check_inference(
        bb, relax.op.nn.conv2d(x0, w3), relax.TensorStructInfo(dtype="float32", ndim=4)
    )
    _check_inference(bb, relax.op.nn.conv2d(x4, w0), relax.TensorStructInfo(dtype="", ndim=4))


def test_conv2d_infer_struct_info_shape_symbolic():
    bb = relax.BlockBuilder()
    n = tir.Var("n", "int64")
    c = tir.Var("c", "int64")
    c16 = tir.Var("c16", "int64")
    ih = tir.Var("ih", "int64")
    iw = tir.Var("iw", "int64")
    ki = tir.Var("ki", "int64")
    ko = tir.Var("ko", "int64")
    kh = tir.Var("kh", "int64")
    kw = tir.Var("kw", "int64")
    stride_h = tir.Var("stride_h", "int64")
    stride_w = tir.Var("stride_w", "int64")
    padding_t = tir.Var("padding_t", "int64")
    padding_l = tir.Var("padding_l", "int64")
    padding_b = tir.Var("padding_b", "int64")
    padding_r = tir.Var("padding_r", "int64")
    dilation_h = tir.Var("dilation_h", "int64")
    dilation_w = tir.Var("dilation_w", "int64")
    x0 = relax.Var("x", R.Tensor((n, c, ih, iw), "float32"))
    x1 = relax.Var("x", R.Tensor((n, c, ih, iw, c16), "float32"))
    w0 = relax.Var("w", R.Tensor((ko, ki, kh, kw), "float32"))
    w1 = relax.Var("w", R.Tensor((ko, c, kh, kw), "float32"))
    w2 = relax.Var("w", R.Tensor((ko, c, kh, kw, c16), "float32"))

    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w0),
        relax.TensorStructInfo((n, ko, ih + 1 - kh, iw + 1 - kw), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w1),
        relax.TensorStructInfo((n, ko, ih + 1 - kh, iw + 1 - kw), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(
            x1, w2, data_layout="NCHW16c", kernel_layout="OIHW16i", out_layout="NCHW"
        ),
        relax.TensorStructInfo((n, ko, ih + 1 - kh, iw + 1 - kw), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(
            x0,
            w0,
            strides=(stride_h, stride_w),
            padding=(padding_t, padding_l, padding_b, padding_r),
            dilation=(dilation_h, dilation_w),
        ),
        relax.TensorStructInfo(
            (
                n,
                ko,
                tvm.tir.div(ih + padding_t + padding_b - dilation_h * (kh - 1) - 1, stride_h) + 1,
                tvm.tir.div(iw + padding_l + padding_r - dilation_w * (kw - 1) - 1, stride_w) + 1,
            ),
            "float32",
        ),
    )


def test_conv2d_infer_struct_info_shape_var():
    bb = relax.BlockBuilder()
    s0 = relax.Var("s", relax.ShapeStructInfo(ndim=4))
    s1 = relax.Var("s", relax.ShapeStructInfo(ndim=5))
    s2 = relax.Var("s", relax.ShapeStructInfo(ndim=4))
    s3 = relax.Var("s", relax.ShapeStructInfo())
    x0 = relax.Var("x", relax.TensorStructInfo(s0, "float32"))
    x1 = relax.Var("x", relax.TensorStructInfo(s1, "float32"))
    x2 = relax.Var("x", relax.TensorStructInfo(s3, "float32"))
    w = relax.Var("w", relax.TensorStructInfo(s2, "float32"))

    _check_inference(bb, relax.op.nn.conv2d(x0, w), relax.TensorStructInfo(dtype="float32", ndim=4))
    _check_inference(
        bb,
        relax.op.nn.conv2d(x1, w, data_layout="NCHW16c"),
        relax.TensorStructInfo(dtype="float32", ndim=5),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w, out_layout="NCHW16c"),
        relax.TensorStructInfo(dtype="float32", ndim=5),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x2, w),
        relax.TensorStructInfo(dtype="float32", ndim=4),
    )


def test_conv2d_infer_struct_info_more_input_dtype():
    bb = relax.BlockBuilder()
    x0 = relax.Var("x", R.Tensor((2, 3, 28, 28), "float16"))
    w0 = relax.Var("w", R.Tensor((4, 3, 3, 3), "float16"))
    x1 = relax.Var("x", R.Tensor((2, 3, 28, 28), "float64"))
    w1 = relax.Var("w", R.Tensor((4, 3, 3, 3), "float64"))
    x2 = relax.Var("x", R.Tensor((2, 3, 28, 28), "int8"))
    w2 = relax.Var("w", R.Tensor((4, 3, 3, 3), "int8"))
    x3 = relax.Var("x", R.Tensor((2, 3, 28, 28), "int32"))
    w3 = relax.Var("w", R.Tensor((4, 3, 3, 3), "int32"))

    _check_inference(
        bb, relax.op.nn.conv2d(x0, w0), relax.TensorStructInfo((2, 4, 26, 26), "float16")
    )
    _check_inference(
        bb, relax.op.nn.conv2d(x1, w1), relax.TensorStructInfo((2, 4, 26, 26), "float64")
    )
    _check_inference(bb, relax.op.nn.conv2d(x2, w2), relax.TensorStructInfo((2, 4, 26, 26), "int8"))
    _check_inference(
        bb, relax.op.nn.conv2d(x3, w3), relax.TensorStructInfo((2, 4, 26, 26), "int32")
    )


def test_conv2d_infer_struct_info_mixed_precision():
    bb = relax.BlockBuilder()
    x0 = relax.Var("x", R.Tensor((2, 3, 28, 28), "float16"))
    w0 = relax.Var("w", R.Tensor((4, 3, 3, 3), "float16"))
    x1 = relax.Var("x", R.Tensor((2, 3, 28, 28), "int8"))
    w1 = relax.Var("w", R.Tensor((4, 3, 3, 3), "int8"))
    x2 = relax.Var("x", R.Tensor((2, 3, 28, 28)))
    w2 = relax.Var("w", R.Tensor((4, 3, 3, 3)))

    _check_inference(
        bb,
        relax.op.nn.conv2d(x0, w0, out_dtype="float32"),
        relax.TensorStructInfo((2, 4, 26, 26), "float32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x1, w1, out_dtype="int32"),
        relax.TensorStructInfo((2, 4, 26, 26), "int32"),
    )
    _check_inference(
        bb,
        relax.op.nn.conv2d(x2, w2, out_dtype="float32"),
        relax.TensorStructInfo((2, 4, 26, 26), "float32"),
    )


def test_conv2d_unequal_input_channel():
    bb = relax.BlockBuilder()
    ic = tir.Var("ic", "int64")
    x0 = relax.Var("x", R.Tensor([2, 3, 28, 28], "float32"))
    w0 = relax.Var("w", R.Tensor([3, 4, 3, 3], "float32"))
    x1 = relax.Var("x", R.Tensor([2, ic, 28, 28], "float32"))
    w1 = relax.Var("w", R.Tensor([4, ic + 2, 3, 3], "float32"))
    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x0, w0))
    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x1, w1))


def test_conv2d_wrong_strides_padding_dilation_length():
    x = relax.Var("x", R.Tensor((2, 3, 28, 28), "float32"))
    w = relax.Var("w", R.Tensor((4, 3, 3, 3), "float32"))
    with pytest.raises(TVMError):
        relax.op.nn.conv2d(x, w, strides=(1, 2, 3))
    with pytest.raises(TVMError):
        relax.op.nn.conv2d(x, w, padding=(1, 2, 3))
    with pytest.raises(TVMError):
        relax.op.nn.conv2d(x, w, dilation=(1, 2, 3))


def test_conv2d_infer_struct_info_wrong_layout_string():
    bb = relax.BlockBuilder()
    x = relax.Var("x", R.Tensor((2, 3, 28, 28), "float32"))
    w = relax.Var("w", R.Tensor((4, 3, 3, 3), "float32"))
    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x, w, data_layout="OIHW"))
    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x, w, kernel_layout="NHWC"))
    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x, w, out_layout="OHWI"))


def test_conv2d_dtype_mismatch():
    bb = relax.BlockBuilder()
    x = relax.Var("x", R.Tensor((2, 3, 28, 28), "float32"))
    w = relax.Var("w", R.Tensor((4, 3, 3, 3), "int8"))

    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x, w))


def test_conv2d_wrong_input_ndim():
    bb = relax.BlockBuilder()
    x0 = relax.Var("x", R.Tensor((2, 3, 28, 28), "float32"))
    x1 = relax.Var("x", R.Tensor((2, 3, 28, 28, 3), "float32"))
    x2 = relax.Var("x", R.Tensor("float32", ndim=3))
    w0 = relax.Var("w", R.Tensor((4, 3, 3, 3), "float32"))
    w1 = relax.Var("w", R.Tensor((4, 3, 6, 3, 3), "float32"))
    w2 = relax.Var("w", R.Tensor("float32", ndim=6))

    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x0, w1))
    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x0, w1, data_layout="NCHW16c"))
    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x0, w2))
    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x1, w0))
    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x2, w0))


def test_conv2d_infer_struct_info_wrong_input_type():
    bb = relax.BlockBuilder()
    x0 = relax.Var("x", R.Tensor((2, 3, 28, 28), "float32"))
    x1 = relax.Var("x", relax.ShapeStructInfo((2, 3, 28, 28)))
    w0 = relax.Var("w", R.Tensor((4, 3, 3, 3), "float32"))
    w1 = relax.Var("w", relax.FuncStructInfo([], R.Tensor((4, 3, 3, 3), "float32")))

    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x0, w1))
    with pytest.raises(TVMError):
        bb.normalize(relax.op.nn.conv2d(x1, w0))


if __name__ == "__main__":
    tvm.testing.main()
