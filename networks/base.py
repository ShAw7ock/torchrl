import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import networks.init as init

class MLPBase(nn.Module):
    def __init__(self, input_shape, hidden_shapes, activation_func=F.relu, init_func = init.basic_init ):
        super().__init__()
        
        self.activation_func = activation_func
        self.fcs = []
        input_shape = np.prod(input_shape)
        for i, next_shape in enumerate( hidden_shapes ):
            fc = nn.Linear(input_shape, next_shape)
            init_func(fc)
            self.fcs.append(fc)
            # set attr for pytorch to track parameters( device )
            self.__setattr__("fc{}".format(i), fc)

            input_shape = next_shape
        
        self.output_shape = hidden_shapes[-1]
    
    def forward(self, x):

        out = x
        for fc in self.fcs:
            out = fc(out)
            out = self.activation_func(out)

        return out

def calc_next_shape(input_shape, conv_info):
    """
    take input shape per-layer conv-info as input
    """
    out_channels, kernel_size, stride, padding = conv_info
    c, h, w = input_shape
    # for padding, dilation, kernel_size, stride in conv_info:
    h = int((h + 2*padding[0] - ( kernel_size[0] - 1 ) - 1 ) / stride[0] + 1)
    w = int((w + 2*padding[1] - ( kernel_size[1] - 1 ) - 1 ) / stride[1] + 1)
    return (out_channels, h, w )

class CNNBase(nn.Module):
    def __init__(self, input_shape, hidden_shapes, activation_func=F.relu, init_func = init.basic_init ):
        super().__init__()
        
        current_shape = input_shape
        in_channels = input_shape[0]
        self.activation_func = activation_func
        self.convs = []
        for i, conv_info in enumerate( hidden_shapes ):
            out_channels, kernel_size, stride, padding = conv_info
            conv = nn.Conv2d( in_channels, out_channels, kernel_size, stride, padding )
            init_func(conv)
            self.convs.append(conv)
            # set attr for pytorch to track parameters( device )
            self.__setattr__("conv{}".format(i), conv)

            in_channels = out_channels
            current_shape = calc_next_shape( current_shape, conv_info )
        
        self.output_shape = current_shape[0] * current_shape[1] * current_shape[2]
    
    def forward(self, x):

        out = x
        for conv in self.convs:
            out = conv(out)
            out = self.activation_func(out)
        
        batch_size = out.size()[0]
        return out.view(batch_size, -1)
