/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

/*!
 * \file convolution.h
 * \brief The functions to make Relax neural network convolution operator calls.
 */

#ifndef TVM_RELAX_OP_NN_CONVOLUTION_H_
#define TVM_RELAX_OP_NN_CONVOLUTION_H_

#include <tvm/relax/attrs/nn.h>

#include <string>
#include <utility>

#include "../op_common.h"

namespace tvm {
namespace relax {

template <typename T>
inline Expr MakeConv(Expr data, Expr weight, Array<PrimExpr> strides, Array<PrimExpr> padding,
                     Array<PrimExpr> dilation, String data_layout, String kernel_layout,
                     String out_layout, DataType out_dtype, std::string op_name) {
  auto attrs = make_object<T>();
  attrs->strides = std::move(strides);
  attrs->padding = std::move(padding);
  attrs->dilation = std::move(dilation);
  attrs->data_layout = std::move(data_layout);
  attrs->kernel_layout = std::move(kernel_layout);
  attrs->out_layout = std::move(out_layout);
  attrs->out_dtype = std::move(out_dtype);
  const Op& op = Op::Get(op_name);
  return Call(op, {data, weight}, Attrs(attrs), {});
}

/*! \brief 2D convolution */
Expr conv2d(Expr data, Expr weight, Array<PrimExpr> strides, Array<PrimExpr> padding,
            Array<PrimExpr> dilation, String data_layout, String kernel_layout,
            Optional<String> out_layout, DataType out_dtype);

}  // namespace relax
}  // namespace tvm

#endif  // TVM_RELAX_OP_NN_CONVOLUTION_H_
